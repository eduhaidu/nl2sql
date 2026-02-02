export default function generateRetryPrompt(nlInput: string, previousQuery: string, errorMessage: string = "") : string {
    return `The following SQL query generated from the natural language input did not execute successfully:

Natural Language Input:
${nlInput}

Generated SQL Query:
${previousQuery}

Error Message:
${errorMessage}

Please generate a revised SQL query that addresses the issues mentioned in the error message. Ensure that the new query accurately reflects the user's original intent while correcting any syntax or logical errors.`;
}