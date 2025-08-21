"""
CrewAI Agent Coordination system for orchestrating the legal document analysis pipeline.

This system handles:
- Agent definitions with roles, goals, and tools
- Sequential task execution pipeline
- Inter-agent communication and data passing
- Error handling and retry logic
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from uuid import UUID

from ..core.config import get_settings
from ..models.document import Document, ProcessedDocument, Clause, DocumentSummary, RiskAssessment
from ..models.base import UserRole, ProcessingStage
from ..core.exceptions import WorkflowError, AnalysisError

# Import our specialized agents
from .ocr_agent import OCRAgent
from .clause_analyzer import ClauseAnalyzerAgent
from .summarizer_agent import SummarizerAgent
from .risk_advisor import RiskAdvisorAgent
from ..services.vector_search import VectorSearchService

logger = logging.getLogger(__name__)
settings = get_settings()


class AgentTask:
    """Represents a task to be executed by an agent."""
    
    def __init__(
        self,
        task_id: str,
        agent_name: str,
        description: str,
        inputs: Dict[str, Any],
        dependencies: List[str] = None
    ):
        self.task_id = task_id
        self.agent_name = agent_name
        self.description = description
        self.inputs = inputs
        self.dependencies = dependencies or []
        self.status = "pending"
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None


class LegalAnalysisCrew:
    """
    CrewAI-style coordination system for legal document analysis.
    
    Orchestrates multiple specialized agents to perform comprehensive
    legal document analysis with proper task sequencing and data flow.
    """
    
    def __init__(self):
        """Initialize the Legal Analysis Crew."""
        # Initialize specialized agents
        self.ocr_agent = OCRAgent()
        self.clause_analyzer = ClauseAnalyzerAgent()
        self.summarizer_agent = SummarizerAgent()
        self.risk_advisor = RiskAdvisorAgent()
        self.vector_search = VectorSearchService()
        
        # Agent registry
        self.agents = {
            "ocr_specialist": {
                "agent": self.ocr_agent,
                "role": "Document OCR Specialist",
                "goal": "Extract and structure text from legal documents with high accuracy",
                "backstory": "Expert in document digitization and layout analysis with years of experience in legal document processing",
                "capabilities": ["pdf_processing", "image_ocr", "text_extraction", "layout_analysis"]
            },
            "clause_analyzer": {
                "agent": self.clause_analyzer,
                "role": "Legal Clause Analyzer", 
                "goal": "Classify and score legal clauses for comprehensive risk assessment",
                "backstory": "Specialized legal analyst with deep expertise in contract analysis and risk identification",
                "capabilities": ["clause_classification", "risk_scoring", "role_analysis", "semantic_analysis"]
            },
            "summarizer": {
                "agent": self.summarizer_agent,
                "role": "Plain Language Translator",
                "goal": "Convert complex legal language into accessible summaries",
                "backstory": "Communication expert specializing in making legal concepts understandable to non-lawyers",
                "capabilities": ["plain_language_conversion", "reading_level_control", "key_points_extraction"]
            },
            "risk_advisor": {
                "agent": self.risk_advisor,
                "role": "Legal Risk Advisor",
                "goal": "Assess risks and provide actionable recommendations for legal documents",
                "backstory": "Senior legal consultant with expertise in risk management and contract negotiation",
                "capabilities": ["risk_assessment", "safer_alternatives", "negotiation_advice", "red_flag_detection"]
            }
        }
        
        # Task execution history
        self.execution_history = []
    
    async def analyze_document(
        self,
        document: Document,
        file_content: bytes,
        user_role: UserRole,
        jurisdiction: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> ProcessedDocument:
        """
        Execute the complete document analysis pipeline.
        
        Args:
            document: Document metadata
            file_content: Raw file content
            user_role: User's role for analysis perspective
            jurisdiction: Legal jurisdiction for context
            progress_callback: Optional callback for progress updates
            
        Returns:
            ProcessedDocument with complete analysis results
            
        Raises:
            WorkflowError: If the analysis pipeline fails
        """
        try:
            logger.info(f"Starting document analysis pipeline for document {document.id}")
            
            # Create task pipeline
            tasks = self._create_analysis_pipeline(
                document, file_content, user_role, jurisdiction
            )
            
            # Execute tasks in sequence
            results = await self._execute_task_pipeline(tasks, progress_callback)
            
            # Assemble final processed document
            processed_doc = await self._assemble_processed_document(
                document, results, user_role
            )
            
            logger.info(f"Document analysis pipeline completed successfully")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Document analysis pipeline failed: {str(e)}")
            raise WorkflowError(f"Analysis pipeline failed: {str(e)}") from e
    
    def _create_analysis_pipeline(
        self,
        document: Document,
        file_content: bytes,
        user_role: UserRole,
        jurisdiction: Optional[str]
    ) -> List[AgentTask]:
        """Create the sequential task pipeline for document analysis."""
        
        tasks = [
            # Task 1: OCR and Text Extraction
            AgentTask(
                task_id="ocr_extraction",
                agent_name="ocr_specialist",
                description="Extract structured text from the legal document",
                inputs={
                    "file_content": file_content,
                    "filename": document.filename,
                    "content_type": document.content_type
                }
            ),
            
            # Task 2: Clause Analysis and Classification
            AgentTask(
                task_id="clause_analysis",
                agent_name="clause_analyzer",
                description="Analyze and classify legal clauses with risk assessment",
                inputs={
                    "user_role": user_role,
                    "jurisdiction": jurisdiction
                },
                dependencies=["ocr_extraction"]
            ),
            
            # Task 3: Vector Indexing (parallel with summarization)
            AgentTask(
                task_id="vector_indexing",
                agent_name="vector_search",
                description="Generate embeddings and index clauses for semantic search",
                inputs={},
                dependencies=["clause_analysis"]
            ),
            
            # Task 4: Document Summarization
            AgentTask(
                task_id="summarization",
                agent_name="summarizer",
                description="Create plain language summary of the document",
                inputs={
                    "user_role": user_role,
                    "jurisdiction": jurisdiction
                },
                dependencies=["clause_analysis"]
            ),
            
            # Task 5: Risk Assessment and Advisory
            AgentTask(
                task_id="risk_assessment",
                agent_name="risk_advisor",
                description="Perform comprehensive risk assessment and generate recommendations",
                inputs={
                    "user_role": user_role,
                    "jurisdiction": jurisdiction,
                    "document_type": None  # Will be determined from summarization
                },
                dependencies=["clause_analysis", "summarization"]
            )
        ]
        
        return tasks
    
    async def _execute_task_pipeline(
        self,
        tasks: List[AgentTask],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Execute the task pipeline with proper dependency management."""
        
        # Create task lookup
        task_lookup = {task.task_id: task for task in tasks}
        completed_tasks = set()
        results = {}
        
        # Execute tasks in dependency order
        while len(completed_tasks) < len(tasks):
            # Find tasks ready to execute
            ready_tasks = []
            for task in tasks:
                if (task.task_id not in completed_tasks and 
                    all(dep in completed_tasks for dep in task.dependencies)):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                raise WorkflowError("Circular dependency or deadlock in task pipeline")
            
            # Execute ready tasks (can be parallel if no dependencies between them)
            task_results = await self._execute_task_batch(ready_tasks, results)
            
            # Update results and completed tasks
            for task_id, result in task_results.items():
                results[task_id] = result
                completed_tasks.add(task_id)
                
                # Update progress
                if progress_callback:
                    progress = len(completed_tasks) / len(tasks) * 100
                    stage = self._get_processing_stage(task_id)
                    await progress_callback(progress, stage)
        
        return results
    
    async def _execute_task_batch(
        self,
        tasks: List[AgentTask],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a batch of tasks that can run in parallel."""
        
        # Create execution coroutines
        task_coroutines = []
        for task in tasks:
            coroutine = self._execute_single_task(task, previous_results)
            task_coroutines.append(coroutine)
        
        # Execute tasks concurrently
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Process results
        task_results = {}
        for i, (task, result) in enumerate(zip(tasks, results)):
            if isinstance(result, Exception):
                logger.error(f"Task {task.task_id} failed: {str(result)}")
                task.status = "failed"
                task.error = str(result)
                raise WorkflowError(f"Task {task.task_id} failed: {str(result)}")
            else:
                task.status = "completed"
                task.result = result
                task_results[task.task_id] = result
        
        return task_results
    
    async def _execute_single_task(
        self,
        task: AgentTask,
        previous_results: Dict[str, Any]
    ) -> Any:
        """Execute a single agent task."""
        
        logger.info(f"Executing task: {task.task_id} ({task.agent_name})")
        task.status = "running"
        task.started_at = datetime.utcnow()
        
        try:
            # Get agent
            if task.agent_name not in self.agents:
                raise WorkflowError(f"Unknown agent: {task.agent_name}")
            
            agent_info = self.agents[task.agent_name]
            agent = agent_info["agent"]
            
            # Prepare inputs with dependency results
            inputs = task.inputs.copy()
            for dep_task_id in task.dependencies:
                if dep_task_id in previous_results:
                    inputs[f"{dep_task_id}_result"] = previous_results[dep_task_id]
            
            # Execute task based on agent type
            result = await self._execute_agent_task(task.agent_name, agent, inputs)
            
            task.completed_at = datetime.utcnow()
            return result
            
        except Exception as e:
            task.completed_at = datetime.utcnow()
            logger.error(f"Task {task.task_id} execution failed: {str(e)}")
            raise
    
    async def _execute_agent_task(
        self,
        agent_name: str,
        agent: Any,
        inputs: Dict[str, Any]
    ) -> Any:
        """Execute a specific agent task based on agent type."""
        
        if agent_name == "ocr_specialist":
            return await agent.process_document(
                inputs["file_content"],
                inputs["filename"],
                inputs["content_type"]
            )
        
        elif agent_name == "clause_analyzer":
            ocr_result = inputs["ocr_extraction_result"]
            return await agent.analyze_clauses(
                ocr_result.text,
                inputs["user_role"],
                inputs.get("jurisdiction")
            )
        
        elif agent_name == "vector_search":
            clauses = inputs["clause_analysis_result"]
            # Index clauses for semantic search
            success = await self.vector_search.index_clauses(clauses)
            return {"indexing_success": success, "indexed_count": len(clauses)}
        
        elif agent_name == "summarizer":
            ocr_result = inputs["ocr_extraction_result"]
            clauses = inputs["clause_analysis_result"]
            return await agent.create_summary(
                ocr_result.text,
                clauses,
                inputs.get("user_role"),
                jurisdiction=inputs.get("jurisdiction")
            )
        
        elif agent_name == "risk_advisor":
            clauses = inputs["clause_analysis_result"]
            summary = inputs.get("summarization_result")
            document_type = summary.document_type if summary else None
            
            return await agent.assess_document_risk(
                clauses,
                inputs["user_role"],
                inputs.get("jurisdiction"),
                document_type
            )
        
        else:
            raise WorkflowError(f"Unknown agent task execution for: {agent_name}")
    
    def _get_processing_stage(self, task_id: str) -> ProcessingStage:
        """Map task ID to processing stage."""
        stage_mapping = {
            "ocr_extraction": ProcessingStage.OCR,
            "clause_analysis": ProcessingStage.ANALYSIS,
            "vector_indexing": ProcessingStage.ANALYSIS,
            "summarization": ProcessingStage.SUMMARIZATION,
            "risk_assessment": ProcessingStage.RISK_ASSESSMENT
        }
        return stage_mapping.get(task_id, ProcessingStage.ANALYSIS)
    
    async def _assemble_processed_document(
        self,
        original_doc: Document,
        results: Dict[str, Any],
        user_role: UserRole
    ) -> ProcessedDocument:
        """Assemble the final ProcessedDocument from task results."""
        
        try:
            # Extract results
            ocr_result = results.get("ocr_extraction")
            clauses = results.get("clause_analysis", [])
            summary = results.get("summarization")
            risk_assessment = results.get("risk_assessment")
            vector_result = results.get("vector_indexing", {})
            
            # Calculate processing time
            processing_time = sum(
                (task.completed_at - task.started_at).total_seconds()
                for task in self.execution_history
                if task.completed_at and task.started_at
            )
            
            # Determine AI models used
            ai_models_used = [
                settings.GEMINI_MODEL_FLASH,  # Used by clause analyzer
                settings.GEMINI_MODEL_PRO,    # Used by summarizer and risk advisor
                "textembedding-gecko@003"     # Used by vector search
            ]
            
            # Create ProcessedDocument
            processed_doc = ProcessedDocument(
                # Copy original document fields
                id=original_doc.id,
                filename=original_doc.filename,
                content_type=original_doc.content_type,
                size_bytes=original_doc.size_bytes,
                user_id=original_doc.user_id,
                jurisdiction=original_doc.jurisdiction,
                user_role=original_doc.user_role,
                storage_url=original_doc.storage_url,
                metadata=original_doc.metadata,
                created_at=original_doc.created_at,
                updated_at=datetime.utcnow(),
                
                # Add processed fields
                structured_text=ocr_result.text if ocr_result else "",
                clauses=clauses,
                summary=summary,
                risk_assessment=risk_assessment,
                processing_time=processing_time,
                ai_models_used=ai_models_used
            )
            
            return processed_doc
            
        except Exception as e:
            logger.error(f"Failed to assemble processed document: {str(e)}")
            raise WorkflowError(f"Failed to assemble results: {str(e)}") from e
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status information for all agents."""
        status = {
            "agents": {},
            "last_execution": None,
            "total_executions": len(self.execution_history)
        }
        
        # Agent status
        for agent_name, agent_info in self.agents.items():
            status["agents"][agent_name] = {
                "role": agent_info["role"],
                "goal": agent_info["goal"],
                "capabilities": agent_info["capabilities"],
                "status": "ready"
            }
        
        # Last execution info
        if self.execution_history:
            last_execution = self.execution_history[-1]
            status["last_execution"] = {
                "task_id": last_execution.task_id,
                "status": last_execution.status,
                "completed_at": last_execution.completed_at
            }
        
        return status
    
    async def execute_custom_workflow(
        self,
        workflow_definition: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a custom workflow definition.
        
        Args:
            workflow_definition: Custom workflow with tasks and dependencies
            inputs: Input data for the workflow
            
        Returns:
            Workflow execution results
        """
        try:
            # Parse workflow definition
            tasks = self._parse_workflow_definition(workflow_definition)
            
            # Add inputs to first task
            if tasks:
                tasks[0].inputs.update(inputs)
            
            # Execute workflow
            results = await self._execute_task_pipeline(tasks)
            
            return {
                "status": "completed",
                "results": results,
                "execution_time": sum(
                    (task.completed_at - task.started_at).total_seconds()
                    for task in tasks
                    if task.completed_at and task.started_at
                )
            }
            
        except Exception as e:
            logger.error(f"Custom workflow execution failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "results": {}
            }
    
    def _parse_workflow_definition(
        self,
        workflow_def: Dict[str, Any]
    ) -> List[AgentTask]:
        """Parse a workflow definition into AgentTask objects."""
        tasks = []
        
        for task_def in workflow_def.get("tasks", []):
            task = AgentTask(
                task_id=task_def["id"],
                agent_name=task_def["agent"],
                description=task_def.get("description", ""),
                inputs=task_def.get("inputs", {}),
                dependencies=task_def.get("dependencies", [])
            )
            tasks.append(task)
        
        return tasks
    
    async def retry_failed_task(
        self,
        task_id: str,
        max_retries: int = 3
    ) -> Any:
        """
        Retry a failed task with exponential backoff.
        
        Args:
            task_id: ID of the task to retry
            max_retries: Maximum number of retry attempts
            
        Returns:
            Task result if successful
        """
        # Find the failed task
        failed_task = None
        for task in self.execution_history:
            if task.task_id == task_id and task.status == "failed":
                failed_task = task
                break
        
        if not failed_task:
            raise WorkflowError(f"No failed task found with ID: {task_id}")
        
        # Retry with exponential backoff
        for attempt in range(max_retries):
            try:
                logger.info(f"Retrying task {task_id}, attempt {attempt + 1}")
                
                # Reset task status
                failed_task.status = "pending"
                failed_task.error = None
                
                # Execute task
                result = await self._execute_single_task(failed_task, {})
                
                logger.info(f"Task {task_id} retry successful")
                return result
                
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Task {task_id} retry {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    failed_task.status = "failed"
                    failed_task.error = str(e)
                    raise WorkflowError(f"Task {task_id} failed after {max_retries} retries: {str(e)}")
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics and performance statistics."""
        if not self.execution_history:
            return {"total_executions": 0}
        
        # Calculate metrics
        total_executions = len(self.execution_history)
        successful_executions = len([t for t in self.execution_history if t.status == "completed"])
        failed_executions = len([t for t in self.execution_history if t.status == "failed"])
        
        # Calculate average execution times by agent
        agent_times = {}
        for task in self.execution_history:
            if task.completed_at and task.started_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                if task.agent_name not in agent_times:
                    agent_times[task.agent_name] = []
                agent_times[task.agent_name].append(duration)
        
        avg_agent_times = {
            agent: sum(times) / len(times)
            for agent, times in agent_times.items()
        }
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "average_execution_times": avg_agent_times,
            "agents_available": len(self.agents)
        }