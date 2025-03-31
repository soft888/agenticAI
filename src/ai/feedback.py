import logging
from typing import Dict, List, Any
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class FeedbackLoop:
    def __init__(self, api_key: str, endpoint: str):
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version="2023-05-15",
            azure_endpoint=endpoint
        )
    
    async def analyze_results(self, user_request: str, plan: List[Dict[str, Any]], 
                              results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the results of the execution and provide feedback."""
        try:
            # Create a prompt for the LLM
            plan_str = json.dumps(plan, indent=2)
            results_str = json.dumps(results, indent=2)
            
            prompt = f"""
            User Request: {user_request}
            
            Plan:
            {plan_str}
            
            Execution Results:
            {results_str}
            
            Analyze the results and provide feedback on the following:
            1. Was the plan successful in fulfilling the user request?
            2. Were there any errors or issues during execution?
            3. How could the plan be improved?
            4. Formulate a response to the user based on the results.
            
            Return your analysis as a JSON object with the following structure:
            {{
                "success": true/false,
                "issues": ["issue1", "issue2", ...],
                "improvements": ["improvement1", "improvement2", ...],
                "user_response": "Message to the user"
            }}
            
            Return only the JSON object, no additional text.
            """
            
            # Call the LLM to analyze the results
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Extract and parse the analysis
            analysis_text = response.choices[0].message.content.strip()
            analysis = json.loads(analysis_text)
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")
            # Return a default analysis in case of error
            return {
                "success": False,
                "issues": [f"Error analyzing results: {str(e)}"],
                "improvements": ["Improve error handling"],
                "user_response": "I encountered an issue while analyzing the results. Please try again."
            }