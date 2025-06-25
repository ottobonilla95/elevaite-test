# import sys
# import time
# import logging
# from typing import Dict, Any
# from hippo_config import HippoRAGConfig
# from triplets_passage import TripletToPassageConverter, main as step2_main
# from generate_embed import EmbeddingGenerator, main as step3_main
# from build_kg import KnowledgeGraphBuilder, main as step4_main
# from index_qdrant import HippoRAGIndexer, main as step5_main
# from elevaite_ingestion.stage.retrieval_stage.hippo_qdrant.retrieval_old import HippoRAGRetriever, main as step6_main
# from generate_response_v2 import HippoRAGAnswerGenerator, main as step7_main
#
# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('hipporag_pipeline.log'),
#         logging.StreamHandler(sys.stdout)
#     ]
# )
# logger = logging.getLogger(__name__)
#
# class HippoRAGPipeline:
#     """Complete HippoRAG pipeline orchestrator"""
#
#     def __init__(self):
#         self.config = None
#         self.execution_log = []
#         self.total_start_time = None
#
#     def log_step(self, step_name: str, status: str, duration: float = None, details: Dict = None):
#         """Log pipeline step execution"""
#         log_entry = {
#             'step': step_name,
#             'status': status,
#             'timestamp': time.time(),
#             'duration_seconds': duration,
#             'details': details or {}
#         }
#         self.execution_log.append(log_entry)
#
#         if status == 'started':
#             logger.info(f"Starting {step_name}...")
#         elif status == 'completed':
#             logger.info(f"✓ {step_name} completed in {duration:.2f}s")
#         elif status == 'failed':
#             logger.error(f"✗ {step_name} failed after {duration:.2f}s")
#
#     def run_step1_config(self) -> bool:
#         """Step 1: Configuration and Setup"""
#         step_start = time.time()
#         self.log_step("Step 1: Configuration", "started")
#
#         try:
#             # Initialize configuration
#             self.config = HippoRAGConfig()
#
#             # Setup Qdrant collections
#             self.config.setup_qdrant_collections()
#
#             # Test triplet loading
#             triplets = self.config.load_triplets()
#
#             duration = time.time() - step_start
#             self.log_step("Step 1: Configuration", "completed", duration, {
#                 'triplets_loaded': len(triplets)
#             })
#             return True
#
#         except Exception as e:
#             duration = time.time() - step_start
#             self.log_step("Step 1: Configuration", "failed", duration, {'error': str(e)})
#             logger.error(f"Step 1 failed: {e}")
#             return False
#
#     def run_step2_passages(self) -> bool:
#         """Step 2: Convert Triplets to Passages"""
#         step_start = time.time()
#         self.log_step("Step 2: Triplet to Passage Conversion", "started")
#
#         try:
#             passages = step2_main()
#
#             duration = time.time() - step_start
#             self.log_step("Step 2: Triplet to Passage Conversion", "completed", duration, {
#                 'passages_created': len(passages)
#             })
#             return True
#
#         except Exception as e:
#             duration = time.time() - step_start
#             self.log_step("Step 2: Triplet to Passage Conversion", "failed", duration, {'error': str(e)})
#             logger.error(f"Step 2 failed: {e}")
#             return False
#
#     def run_step3_embeddings(self) -> bool:
#         """Step 3: Generate Embeddings"""
#         step_start = time.time()
#         self.log_step("Step 3: Embedding Generation", "started")
#
#         try:
#             stats = step3_main()
#
#             duration = time.time() - step_start
#             self.log_step("Step 3: Embedding Generation", "completed", duration, {
#                 'collection_stats': stats
#             })
#             return True
#
#         except Exception as e:
#             duration = time.time() - step_start
#             self.log_step("Step 3: Embedding Generation", "failed", duration, {'error': str(e)})
#             logger.error(f"Step 3 failed: {e}")
#             return False
#
#     def run_step4_graph(self) -> bool:
#         """Step 4: Build Knowledge Graph"""
#         step_start = time.time()
#         self.log_step("Step 4: Knowledge Graph Construction", "started")
#
#         try:
#             stats = step4_main()
#
#             duration = time.time() - step_start
#             self.log_step("Step 4: Knowledge Graph Construction", "completed", duration, {
#                 'graph_stats': stats
#             })
#             return True
#
#         except Exception as e:
#             duration = time.time() - step_start
#             self.log_step("Step 4: Knowledge Graph Construction", "failed", duration, {'error': str(e)})
#             logger.error(f"Step 4 failed: {e}")
#             return False
#
#     def run_step5_indexing(self) -> bool:
#         """Step 5: Indexing and Storage"""
#         step_start = time.time()
#         self.log_step("Step 5: Indexing & Storage", "started")
#
#         try:
#             index, integrity_report = step5_main()
#
#             duration = time.time() - step_start
#             self.log_step("Step 5: Indexing & Storage", "completed", duration, {
#                 'index_metadata': index.get('metadata', {}),
#                 'integrity_report': integrity_report
#             })
#             return True
#
#         except Exception as e:
#             duration = time.time() - step_start
#             self.log_step("Step 5: Indexing & Storage", "failed", duration, {'error': str(e)})
#             logger.error(f"Step 5 failed: {e}")
#             return False
#
#     def run_step6_retrieval(self) -> bool:
#         """Step 6: Test Retrieval System"""
#         step_start = time.time()
#         self.log_step("Step 6: Retrieval System", "started")
#
#         try:
#             results = step6_main()
#
#             duration = time.time() - step_start
#             self.log_step("Step 6: Retrieval System", "completed", duration, {
#                 'test_queries': len(results)
#             })
#             return True
#
#         except Exception as e:
#             duration = time.time() - step_start
#             self.log_step("Step 6: Retrieval System", "failed", duration, {'error': str(e)})
#             logger.error(f"Step 6 failed: {e}")
#             return False
#
#     def run_step7_generation(self) -> bool:
#         """Step 7: Test Answer Generation"""
#         step_start = time.time()
#         self.log_step("Step 7: Answer Generation", "started")
#
#         try:
#             results = step7_main()
#
#             duration = time.time() - step_start
#             self.log_step("Step 7: Answer Generation", "completed", duration, {
#                 'test_answers': len(results)
#             })
#             return True
#
#         except Exception as e:
#             duration = time.time() - step_start
#             self.log_step("Step 7: Answer Generation", "failed", duration, {'error': str(e)})
#             logger.error(f"Step 7 failed: {e}")
#             return False
#
#     def run_complete_pipeline(self, steps_to_run: list = None) -> Dict[str, Any]:
#         """Run the complete HippoRAG pipeline"""
#         self.total_start_time = time.time()
#
#         if steps_to_run is None:
#             steps_to_run = [1, 2, 3, 4, 5, 6, 7]
#
#         logger.info("="*60)
#         logger.info("Starting HippoRAG Complete Pipeline")
#         logger.info(f"Steps to run: {steps_to_run}")
#         logger.info("="*60)
#
#         # Pipeline steps
#         pipeline_steps = {
#             1: self.run_step1_config,
#             2: self.run_step2_passages,
#             3: self.run_step3_embeddings,
#             4: self.run_step4_graph,
#             5: self.run_step5_indexing,
#             6: self.run_step6_retrieval,
#             7: self.run_step7_generation
#         }
#
#         # Execute steps
#         completed_steps = []
#         failed_steps = []
#
#         for step_num in steps_to_run:
#             if step_num in pipeline_steps:
#                 success = pipeline_steps[step_num]()
#                 if success:
#                     completed_steps.append(step_num)
#                 else:
#                     failed_steps.append(step_num)
#                     # Stop pipeline on failure
#                     logger.error(f"Pipeline stopped due to failure in Step {step_num}")
#                     break
#             else:
#                 logger.warning(f"Invalid step number: {step_num}")
#
#         total_duration = time.time() - self.total_start_time
#
#         # Generate pipeline report
#         pipeline_result = {
#             'success': len(failed_steps) == 0,
#             'completed_steps': completed_steps,
#             'failed_steps': failed_steps,
#             'total_duration_seconds': total_duration,
#             'execution_log': self.execution_log
#         }
#
#         # Print summary
#         self.print_pipeline_summary(pipeline_result)
#
#         return pipeline_result
#
#     def print_pipeline_summary(self, result: Dict[str, Any]):
#         """Print pipeline execution summary"""
#         logger.info("="*60)
#         logger.info("HippoRAG Pipeline Execution Summary")
#         logger.info("="*60)
#
#         logger.info(f"Overall Status: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
#         logger.info(f"Total Duration: {result['total_duration_seconds']:.2f} seconds")
#         logger.info(f"Completed Steps: {result['completed_steps']}")
#
#         if result['failed_steps']:
#             logger.info(f"Failed Steps: {result['failed_steps']}")
#
#         logger.info("\nStep-by-step breakdown:")
#         for log_entry in result['execution_log']:
#             if log_entry['status'] == 'completed':
#                 logger.info(f"  ✓ {log_entry['step']}: {log_entry['duration_seconds']:.2f}s")
#             elif log_entry['status'] == 'failed':
#                 logger.info(f"  ✗ {log_entry['step']}: {log_entry['duration_seconds']:.2f}s")
#
#         if result['success']:
#             logger.info("\n🎉 HippoRAG pipeline completed successfully!")
#             logger.info("You can now use the system for question answering.")
#             logger.info("Run 'python step7_answer_generation.py' for interactive Q&A.")
#         else:
#             logger.info("\n❌ Pipeline failed. Check the logs above for details.")
#
#         logger.info("="*60)
#
# def main():
#     """Main execution function"""
#     import argparse
#
#     parser = argparse.ArgumentParser(description='Run HippoRAG Pipeline')
#     parser.add_argument('--steps', nargs='+', type=int, default=[1,2,3,4,5,6,7],
#                        help='Steps to run (default: all steps 1-7)')
#     parser.add_argument('--config-only', action='store_true',
#                        help='Run only configuration step')
#
#     args = parser.parse_args()
#
#     if args.config_only:
#         steps_to_run = [1]
#     else:
#         steps_to_run = args.steps
#
#     # Run pipeline
#     pipeline = HippoRAGPipeline()
#     result = pipeline.run_complete_pipeline(steps_to_run)
#
#     # Exit with appropriate code
#     sys.exit(0 if result['success'] else 1)
#
# if __name__ == "__main__":
#     main()