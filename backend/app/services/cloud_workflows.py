"""
Cloud Workflows integration for orchestrating the legal document analysis pipeline.

This service handles:
- Workflow YAML definition for agent pipeline orchestration
- Error handling and retry logic in workflows
- Job status tracking and progress updates
- Integration with Google Cloud Workflows
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml

from google.cloud import workflows_v1
from google.cloud.workflows import executions_v1
from google.api_core import exceptions as gcp_exceptions

from ..core.config import get_settings
from ..models.base import ProcessingStage, ProcessingStatus
from ..core.exceptions import WorkflowError

logger = logging.getLogger(__name__)
settings = get_settings()


class CloudWorkflowsService:
    """
    Service for integrating with Google Cloud Workflows to orchestrate
    the legal document analysis pipeline with robust error handling.
    """
    
    def __init__(self):
        """Initialize Cloud Workflows service."""
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.VERTEX_AI_LOCATION
        
        # Initialize clients
        try:
            self.workflows_client = workflows_v1.WorkflowsClient()
            self.executions_client = executions_v1.ExecutionsClient()
            logger.info("Cloud Workflows clients initialized successfully")
        except Exception as e:
            logger.warning(f"Cloud Workflows initialization failed: {str(e)}")
            self.workflows_client = None
            self.executions_client = None
        
        # Workflow definitions
        self.workflow_definitions = {
            "legal_document_analysis": self._get_legal_analysis_workflow(),
            "clause_reanalysis": self._get_clause_reanalysis_workflow(),
            "risk_assessment_only": self._get_risk_assessment_workflow()
        }
    
    def _get_legal_analysis_workflow(self) -> Dict[str, Any]:
        """Get the main legal document analysis workflow definition."""
        return {
            "main": {
                "params": ["input"],
                "steps": [
                    {
                        "init": {
                            "assign": [
                                {"document_id": "${input.document_id}"},
                                {"user_role": "${input.user_role}"},
                                {"jurisdiction": "${input.jurisdiction}"},
                                {"api_base_url": "${input.api_base_url}"},
                                {"retry_count": 0},
                                {"max_retries": 3}
                            ]
                        }
                    },
                    {
                        "update_status_processing": {
                            "call": "http.post",
                            "args": {
                                "url": "${api_base_url}/v1/jobs/${document_id}/status",
                                "body": {
                                    "status": "processing",
                                    "stage": "ocr",
                                    "progress": 10
                                },
                                "headers": {
                                    "Content-Type": "application/json"
                                }
                            }
                        }
                    },
                    {
                        "ocr_step": {
                            "try": {
                                "call": "http.post",
                                "args": {
                                    "url": "${api_base_url}/v1/agents/ocr/process",
                                    "body": {
                                        "document_id": "${document_id}"
                                    },
                                    "headers": {
                                        "Content-Type": "application/json"
                                    }
                                },
                                "result": "ocr_result"
                            },
                            "retry": {
                                "predicate": "${http.default_retry_predicate}",
                                "max_retries": 3,
                                "backoff": {
                                    "initial_delay": 2,
                                    "max_delay": 60,
                                    "multiplier": 2
                                }
                            },
                            "except": {
                                "as": "e",
                                "steps": [
                                    {
                                        "log_ocr_error": {
                                            "call": "sys.log",
                                            "args": {
                                                "text": "${'OCR processing failed: ' + e.message}",
                                                "severity": "ERROR"
                                            }
                                        }
                                    },
                                    {
                                        "update_status_failed": {
                                            "call": "http.post",
                                            "args": {
                                                "url": "${api_base_url}/v1/jobs/${document_id}/status",
                                                "body": {
                                                    "status": "failed",
                                                    "stage": "ocr",
                                                    "error": "${e.message}"
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "raise_error": {
                                            "raise": "${e}"
                                        }
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "update_status_analysis": {
                            "call": "http.post",
                            "args": {
                                "url": "${api_base_url}/v1/jobs/${document_id}/status",
                                "body": {
                                    "status": "processing",
                                    "stage": "analysis",
                                    "progress": 30
                                }
                            }
                        }
                    },
                    {
                        "clause_analysis_step": {
                            "try": {
                                "call": "http.post",
                                "args": {
                                    "url": "${api_base_url}/v1/agents/clause-analyzer/analyze",
                                    "body": {
                                        "document_id": "${document_id}",
                                        "user_role": "${user_role}",
                                        "jurisdiction": "${jurisdiction}",
                                        "ocr_result": "${ocr_result}"
                                    }
                                },
                                "result": "clause_analysis_result"
                            },
                            "retry": {
                                "predicate": "${http.default_retry_predicate}",
                                "max_retries": 3,
                                "backoff": {
                                    "initial_delay": 2,
                                    "max_delay": 60,
                                    "multiplier": 2
                                }
                            },
                            "except": {
                                "as": "e",
                                "steps": [
                                    {
                                        "log_analysis_error": {
                                            "call": "sys.log",
                                            "args": {
                                                "text": "${'Clause analysis failed: ' + e.message}",
                                                "severity": "ERROR"
                                            }
                                        }
                                    },
                                    {
                                        "update_status_failed": {
                                            "call": "http.post",
                                            "args": {
                                                "url": "${api_base_url}/v1/jobs/${document_id}/status",
                                                "body": {
                                                    "status": "failed",
                                                    "stage": "analysis",
                                                    "error": "${e.message}"
                                                }
                                            }
                                        }
                                    },
                                    {
                                        "raise_error": {
                                            "raise": "${e}"
                                        }
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "parallel_processing": {
                            "parallel": {
                                "shared": ["document_id", "user_role", "jurisdiction", "api_base_url"],
                                "branches": [
                                    {
                                        "summarization_branch": {
                                            "steps": [
                                                {
                                                    "update_status_summarization": {
                                                        "call": "http.post",
                                                        "args": {
                                                            "url": "${api_base_url}/v1/jobs/${document_id}/status",
                                                            "body": {
                                                                "status": "processing",
                                                                "stage": "summarization",
                                                                "progress": 50
                                                            }
                                                        }
                                                    }
                                                },
                                                {
                                                    "summarization_step": {
                                                        "try": {
                                                            "call": "http.post",
                                                            "args": {
                                                                "url": "${api_base_url}/v1/agents/summarizer/summarize",
                                                                "body": {
                                                                    "document_id": "${document_id}",
                                                                    "user_role": "${user_role}",
                                                                    "jurisdiction": "${jurisdiction}",
                                                                    "clause_analysis": "${clause_analysis_result}"
                                                                }
                                                            },
                                                            "result": "summary_result"
                                                        },
                                                        "retry": {
                                                            "predicate": "${http.default_retry_predicate}",
                                                            "max_retries": 2
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "vector_indexing_branch": {
                                            "steps": [
                                                {
                                                    "vector_indexing_step": {
                                                        "try": {
                                                            "call": "http.post",
                                                            "args": {
                                                                "url": "${api_base_url}/v1/agents/vector-search/index",
                                                                "body": {
                                                                    "document_id": "${document_id}",
                                                                    "clauses": "${clause_analysis_result}"
                                                                }
                                                            },
                                                            "result": "vector_result"
                                                        },
                                                        "retry": {
                                                            "predicate": "${http.default_retry_predicate}",
                                                            "max_retries": 2
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "update_status_risk_assessment": {
                            "call": "http.post",
                            "args": {
                                "url": "${api_base_url}/v1/jobs/${document_id}/status",
                                "body": {
                                    "status": "processing",
                                    "stage": "risk_assessment",
                                    "progress": 80
                                }
                            }
                        }
                    },
                    {
                        "risk_assessment_step": {
                            "try": {
                                "call": "http.post",
                                "args": {
                                    "url": "${api_base_url}/v1/agents/risk-advisor/assess",
                                    "body": {
                                        "document_id": "${document_id}",
                                        "user_role": "${user_role}",
                                        "jurisdiction": "${jurisdiction}",
                                        "clauses": "${clause_analysis_result}",
                                        "summary": "${summary_result}"
                                    }
                                },
                                "result": "risk_assessment_result"
                            },
                            "retry": {
                                "predicate": "${http.default_retry_predicate}",
                                "max_retries": 2
                            }
                        }
                    },
                    {
                        "finalize_results": {
                            "call": "http.post",
                            "args": {
                                "url": "${api_base_url}/v1/jobs/${document_id}/complete",
                                "body": {
                                    "status": "completed",
                                    "progress": 100,
                                    "results": {
                                        "ocr": "${ocr_result}",
                                        "clauses": "${clause_analysis_result}",
                                        "summary": "${summary_result}",
                                        "risk_assessment": "${risk_assessment_result}",
                                        "vector_indexing": "${vector_result}"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "return_result": {
                            "return": {
                                "status": "completed",
                                "document_id": "${document_id}",
                                "results": {
                                    "ocr": "${ocr_result}",
                                    "clauses": "${clause_analysis_result}",
                                    "summary": "${summary_result}",
                                    "risk_assessment": "${risk_assessment_result}"
                                }
                            }
                        }
                    }
                ]
            }
        }
    
    def _get_clause_reanalysis_workflow(self) -> Dict[str, Any]:
        """Get workflow for re-analyzing specific clauses."""
        return {
            "main": {
                "params": ["input"],
                "steps": [
                    {
                        "init": {
                            "assign": [
                                {"document_id": "${input.document_id}"},
                                {"clause_ids": "${input.clause_ids}"},
                                {"user_role": "${input.user_role}"},
                                {"api_base_url": "${input.api_base_url}"}
                            ]
                        }
                    },
                    {
                        "reanalyze_clauses": {
                            "call": "http.post",
                            "args": {
                                "url": "${api_base_url}/v1/agents/clause-analyzer/reanalyze",
                                "body": {
                                    "document_id": "${document_id}",
                                    "clause_ids": "${clause_ids}",
                                    "user_role": "${user_role}"
                                }
                            },
                            "result": "reanalysis_result"
                        }
                    },
                    {
                        "update_document": {
                            "call": "http.post",
                            "args": {
                                "url": "${api_base_url}/v1/documents/${document_id}/update-clauses",
                                "body": {
                                    "updated_clauses": "${reanalysis_result}"
                                }
                            }
                        }
                    },
                    {
                        "return_result": {
                            "return": {
                                "status": "completed",
                                "updated_clauses": "${reanalysis_result}"
                            }
                        }
                    }
                ]
            }
        }
    
    def _get_risk_assessment_workflow(self) -> Dict[str, Any]:
        """Get workflow for risk assessment only."""
        return {
            "main": {
                "params": ["input"],
                "steps": [
                    {
                        "init": {
                            "assign": [
                                {"document_id": "${input.document_id}"},
                                {"user_role": "${input.user_role}"},
                                {"jurisdiction": "${input.jurisdiction}"},
                                {"api_base_url": "${input.api_base_url}"}
                            ]
                        }
                    },
                    {
                        "get_document_data": {
                            "call": "http.get",
                            "args": {
                                "url": "${api_base_url}/v1/documents/${document_id}"
                            },
                            "result": "document_data"
                        }
                    },
                    {
                        "risk_assessment": {
                            "call": "http.post",
                            "args": {
                                "url": "${api_base_url}/v1/agents/risk-advisor/assess",
                                "body": {
                                    "document_id": "${document_id}",
                                    "user_role": "${user_role}",
                                    "jurisdiction": "${jurisdiction}",
                                    "clauses": "${document_data.clauses}"
                                }
                            },
                            "result": "risk_result"
                        }
                    },
                    {
                        "return_result": {
                            "return": {
                                "status": "completed",
                                "risk_assessment": "${risk_result}"
                            }
                        }
                    }
                ]
            }
        }
    
    async def create_workflow(
        self,
        workflow_name: str,
        workflow_definition: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create or update a Cloud Workflow.
        
        Args:
            workflow_name: Name of the workflow
            workflow_definition: Custom workflow definition (optional)
            
        Returns:
            Workflow resource name
            
        Raises:
            WorkflowError: If workflow creation fails
        """
        try:
            if not self.workflows_client:
                raise WorkflowError("Cloud Workflows client not initialized")
            
            # Use provided definition or get from predefined workflows
            if workflow_definition:
                definition = workflow_definition
            elif workflow_name in self.workflow_definitions:
                definition = self.workflow_definitions[workflow_name]
            else:
                raise WorkflowError(f"Unknown workflow: {workflow_name}")
            
            # Convert to YAML format
            workflow_yaml = yaml.dump(definition, default_flow_style=False)
            
            # Create workflow request
            parent = f"projects/{self.project_id}/locations/{self.location}"
            workflow = workflows_v1.Workflow(
                name=f"{parent}/workflows/{workflow_name}",
                source_contents=workflow_yaml,
                description=f"Legal document analysis workflow: {workflow_name}"
            )
            
            request = workflows_v1.CreateWorkflowRequest(
                parent=parent,
                workflow=workflow,
                workflow_id=workflow_name
            )
            
            # Create or update workflow
            try:
                operation = await asyncio.get_event_loop().run_in_executor(
                    None, self.workflows_client.create_workflow, request
                )
                result = operation.result()
                logger.info(f"Created workflow: {result.name}")
                return result.name
                
            except gcp_exceptions.AlreadyExists:
                # Update existing workflow
                update_request = workflows_v1.UpdateWorkflowRequest(
                    workflow=workflow
                )
                operation = await asyncio.get_event_loop().run_in_executor(
                    None, self.workflows_client.update_workflow, update_request
                )
                result = operation.result()
                logger.info(f"Updated workflow: {result.name}")
                return result.name
            
        except Exception as e:
            logger.error(f"Workflow creation failed: {str(e)}")
            raise WorkflowError(f"Failed to create workflow: {str(e)}") from e
    
    async def execute_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        execution_id: Optional[str] = None
    ) -> str:
        """
        Execute a Cloud Workflow.
        
        Args:
            workflow_name: Name of the workflow to execute
            input_data: Input data for the workflow
            execution_id: Optional custom execution ID
            
        Returns:
            Execution ID
            
        Raises:
            WorkflowError: If workflow execution fails
        """
        try:
            if not self.executions_client:
                raise WorkflowError("Cloud Workflows executions client not initialized")
            
            # Prepare execution request
            parent = f"projects/{self.project_id}/locations/{self.location}/workflows/{workflow_name}"
            
            execution = executions_v1.Execution(
                argument=json.dumps(input_data)
            )
            
            request = executions_v1.CreateExecutionRequest(
                parent=parent,
                execution=execution
            )
            
            # Execute workflow
            execution_result = await asyncio.get_event_loop().run_in_executor(
                None, self.executions_client.create_execution, request
            )
            
            execution_id = execution_result.name.split('/')[-1]
            logger.info(f"Started workflow execution: {execution_id}")
            
            return execution_id
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            raise WorkflowError(f"Failed to execute workflow: {str(e)}") from e
    
    async def get_execution_status(
        self,
        workflow_name: str,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of a workflow execution.
        
        Args:
            workflow_name: Name of the workflow
            execution_id: Execution ID
            
        Returns:
            Execution status information
        """
        try:
            if not self.executions_client:
                return {"status": "unknown", "error": "Client not initialized"}
            
            # Get execution details
            name = f"projects/{self.project_id}/locations/{self.location}/workflows/{workflow_name}/executions/{execution_id}"
            
            execution = await asyncio.get_event_loop().run_in_executor(
                None, self.executions_client.get_execution, {"name": name}
            )
            
            # Parse execution status
            status_info = {
                "execution_id": execution_id,
                "state": execution.state.name,
                "start_time": execution.start_time,
                "end_time": execution.end_time,
                "duration": None
            }
            
            # Calculate duration if completed
            if execution.start_time and execution.end_time:
                duration = execution.end_time - execution.start_time
                status_info["duration"] = duration.total_seconds()
            
            # Add result or error
            if execution.state == executions_v1.Execution.State.SUCCEEDED:
                if execution.result:
                    status_info["result"] = json.loads(execution.result)
            elif execution.state == executions_v1.Execution.State.FAILED:
                if execution.error:
                    status_info["error"] = {
                        "message": execution.error.payload,
                        "stack_trace": execution.error.context
                    }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get execution status: {str(e)}")
            return {
                "execution_id": execution_id,
                "status": "error",
                "error": str(e)
            }
    
    async def cancel_execution(
        self,
        workflow_name: str,
        execution_id: str
    ) -> bool:
        """
        Cancel a running workflow execution.
        
        Args:
            workflow_name: Name of the workflow
            execution_id: Execution ID to cancel
            
        Returns:
            True if cancellation was successful
        """
        try:
            if not self.executions_client:
                return False
            
            name = f"projects/{self.project_id}/locations/{self.location}/workflows/{workflow_name}/executions/{execution_id}"
            
            request = executions_v1.CancelExecutionRequest(name=name)
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.executions_client.cancel_execution, request
            )
            
            logger.info(f"Cancelled workflow execution: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel execution: {str(e)}")
            return False
    
    async def list_executions(
        self,
        workflow_name: str,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List recent executions for a workflow.
        
        Args:
            workflow_name: Name of the workflow
            page_size: Number of executions to return
            
        Returns:
            List of execution information
        """
        try:
            if not self.executions_client:
                return []
            
            parent = f"projects/{self.project_id}/locations/{self.location}/workflows/{workflow_name}"
            
            request = executions_v1.ListExecutionsRequest(
                parent=parent,
                page_size=page_size
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self.executions_client.list_executions, request
            )
            
            executions = []
            for execution in response.executions:
                execution_id = execution.name.split('/')[-1]
                executions.append({
                    "execution_id": execution_id,
                    "state": execution.state.name,
                    "start_time": execution.start_time,
                    "end_time": execution.end_time
                })
            
            return executions
            
        except Exception as e:
            logger.error(f"Failed to list executions: {str(e)}")
            return []
    
    def get_workflow_yaml(self, workflow_name: str) -> str:
        """
        Get the YAML definition for a workflow.
        
        Args:
            workflow_name: Name of the workflow
            
        Returns:
            YAML workflow definition
        """
        if workflow_name not in self.workflow_definitions:
            raise WorkflowError(f"Unknown workflow: {workflow_name}")
        
        definition = self.workflow_definitions[workflow_name]
        return yaml.dump(definition, default_flow_style=False)
    
    async def validate_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a workflow definition.
        
        Args:
            workflow_definition: Workflow definition to validate
            
        Returns:
            Validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Basic structure validation
            if "main" not in workflow_definition:
                validation_result["errors"].append("Missing 'main' section")
                validation_result["valid"] = False
            
            main_section = workflow_definition.get("main", {})
            
            if "steps" not in main_section:
                validation_result["errors"].append("Missing 'steps' in main section")
                validation_result["valid"] = False
            
            # Validate steps
            steps = main_section.get("steps", [])
            if not isinstance(steps, list):
                validation_result["errors"].append("Steps must be a list")
                validation_result["valid"] = False
            
            # Check for required parameters
            params = main_section.get("params", [])
            if "input" not in params:
                validation_result["warnings"].append("Consider adding 'input' parameter")
            
            # Validate YAML syntax
            try:
                yaml.dump(workflow_definition)
            except yaml.YAMLError as e:
                validation_result["errors"].append(f"Invalid YAML syntax: {str(e)}")
                validation_result["valid"] = False
            
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
        
        return validation_result