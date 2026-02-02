'use client';
import axios from "axios";
import ImportDB from "./importdb";
import MessageBubble from "./MessageBubble";
import ResultTable from "./ResultTable";
import { useState, useEffect } from "react";
import generateRetryPrompt from "./util/GenerateRetryPrompt";

export default function Home() {
  const [messages, setMessages] = useState<{ message: string; isUser: boolean }[]>([]);
  const [showImportDB, setShowImportDB] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [queryResult, setQueryResult] = useState<any[] | null>(null);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [currentNLInput, setCurrentNLInput] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showRetryOption, setShowRetryOption] = useState(false);
  const [showRetryEditor, setShowRetryEditor] = useState(false);
  const [retryPrompt, setRetryPrompt] = useState<string>("");
  
  // Cleanup session on page unload
  useEffect(() => {
    const handleBeforeUnload = async () => {
      if (sessionId) {
        // Use sendBeacon for reliable cleanup on page unload
        navigator.sendBeacon(`http://127.0.0.1:8000/disconnect/${sessionId}`);
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      // Cleanup on component unmount
      if (sessionId) {
        axios.delete(`http://127.0.0.1:8000/disconnect/${sessionId}`).catch(console.error);
      }
    };
  }, [sessionId]);
  
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>)=>{
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const nlInput = formData.get("nl-input") as string;
    console.log("Natural Language Input:", nlInput);
    setMessages(prevMessages => [...prevMessages, { message: nlInput, isUser: true }]);
    setCurrentNLInput(nlInput);
    setShowRetryOption(false); // Reset retry option for new query
    setShowRetryEditor(false); // Close any open retry editor
    const sendMessage = async (message: string) => {
      if (!sessionId){
        alert("Please import a database first.");
        return;
      }
      try{
        const response = await axios.post("http://127.0.0.1:8000/nlinput",{
          nl_input: message,
          session_id: sessionId
        });
        console.log("Response from backend:", response.data);
        const AIMessage = response.data.response;
        const generatedQuery = response.data.query;
        setMessages(prevMessages => [...prevMessages, { message: AIMessage, isUser: false }]);
        // Return the query so we can use it immediately
        return generatedQuery;
      } catch (error) {
        console.error("Error sending message:", error);
        return null;
      }
    }
    const query = await sendMessage(nlInput);
    if (query) {
      setCurrentQuery(query);
      const errorMsg = await executeQuery(query);
      if (errorMsg && errorMsg !== "Query executed successfully.") {
        // Generate retry prompt and show editor instead of auto-sending
        const generatedRetryPrompt = generateRetryPrompt(nlInput, query, errorMsg);
        setRetryPrompt(generatedRetryPrompt);
        setErrorMessage(errorMsg);
        setShowRetryEditor(true);
      }
    }
    // event.currentTarget.reset();
  };

  const executeQuery = async (query: string) => {
    if (!sessionId){
      alert("Please import a database first.");
      return;
    }
    try{
      const response = await axios.post(`http://127.0.0.1:8000/executesql/${sessionId}`, {
        query: query
      });
      console.log("Query execution result:", response.data);
      // Check if result is an array before setting
      if (Array.isArray(response.data.result)) {
        setQueryResult(response.data.result);
        setShowRetryOption(true); // Show retry option for successful queries
        setErrorMessage(null); // Clear any previous error
      } else {
        // Handle non-array results (e.g., INSERT, UPDATE, DELETE confirmations)
        const errorMsg = response.data.result || "Query executed successfully.";
        setQueryResult(null);
        setMessages(prevMessages => [...prevMessages, { 
          message: typeof response.data.result === 'string' 
            ? response.data.result 
            : JSON.stringify(response.data.result), 
          isUser: false 
        }]);
        return errorMsg;
      }
    } catch (error) {
      console.error("Error executing query:", error);
    }
  }
  
  const retryGenerateQuery = async (editedPrompt: string) => {
    if (!sessionId){
      alert("Please import a database first.");
      return;
    }
    try{
      // Add the user's edited retry prompt to messages
      setMessages(prevMessages => [...prevMessages, { message: editedPrompt, isUser: true }]);
      
      // Send the edited prompt as a new NL input
      const response = await axios.post("http://127.0.0.1:8000/nlinput", {
        nl_input: editedPrompt,
        session_id: sessionId
      });
      console.log("Retry response from backend:", response.data);
      const AIMessage = response.data.response;
      const newGeneratedQuery = response.data.query;
      setMessages(prevMessages => [...prevMessages, { message: AIMessage, isUser: false }]);
      
      // Execute the new query
      setCurrentQuery(newGeneratedQuery);
      await executeQuery(newGeneratedQuery);
      
      // Close the retry editor
      setShowRetryEditor(false);
      setRetryPrompt("");
    }
    catch (error) {
      console.error("Error retrying query generation:", error);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold mb-8">Welcome to the NL2SQL Interface</h1>
      <div className="fixed top-4 right-4">
        <button
          onClick={() => setShowImportDB(true)}
          className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600"
        >
          Import DB
        </button>
      </div>
      
      {showImportDB && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 relative">
        <button
          onClick={() => setShowImportDB(false)}
          className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
        <ImportDB setSessionId={setSessionId} currentSessionId={sessionId} />
          </div>
        </div>
      )}
      
      <div className="w-full max-w-xl mb-6">
        {messages.map((msg, index)=>(
          <MessageBubble key={index} message={msg.message} isUser={msg.isUser} />
        ))}
      </div>
      
      {showRetryEditor && (
        <div className="w-full max-w-4xl mb-6 bg-yellow-50 border-2 border-yellow-400 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-2 text-gray-800">Query Error - Retry Prompt</h2>
          <div className="mb-4">
            <p className="text-sm text-gray-600 mb-2"><strong>Error:</strong> {errorMessage}</p>
            <p className="text-sm text-gray-600 mb-2"><strong>Failed Query:</strong></p>
            <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">{currentQuery}</pre>
          </div>
          <label htmlFor="retry-prompt" className="block mb-2 text-sm font-medium text-gray-700">
            Review and edit the retry prompt before sending:
          </label>
          <textarea
            id="retry-prompt"
            value={retryPrompt}
            onChange={(e) => setRetryPrompt(e.target.value)}
            className="w-full border border-gray-300 rounded-md p-3 mb-4 font-mono text-sm"
            rows={8}
          />
          <div className="flex gap-2">
            <button
              onClick={() => retryGenerateQuery(retryPrompt)}
              className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
            >
              Send Retry Prompt
            </button>
            <button
              onClick={() => {
                setShowRetryEditor(false);
                setRetryPrompt("");
              }}
              className="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      
      {queryResult && (
      <div className="w-full max-w-4xl mb-6">
        <h2 className="text-2xl font-semibold mb-4">Query Results:</h2>
        <ResultTable result={queryResult} />
      </div>
      )}

      {showRetryOption && (!errorMessage || errorMessage === "Query executed successfully." || errorMessage==="") && (
        <div className="w-full max-w-4xl mb-4 bg-blue-50 border border-blue-300 rounded-lg p-4">
          <p className="text-gray-700 mb-3">Is the result not what you expected?</p>
          <button
            onClick={() => {
              // Generate retry prompt for unsuccessful result (not error)
              const generatedRetryPrompt = generateRetryPrompt(
                currentNLInput, 
                currentQuery, 
                "The query executed successfully but did not return the expected results."
              );
              setRetryPrompt(generatedRetryPrompt);
              setShowRetryEditor(true);
              setShowRetryOption(false);
            }}
            className="bg-yellow-500 text-white px-4 py-2 rounded-md hover:bg-yellow-600"
          >
            Revise Query
          </button>
        </div>
      )}
      
      <form action="submit" className="flex flex-col items-start" onSubmit={handleSubmit}>
        <label htmlFor="nl-input" className="block mb-2 text-lg font-medium text-gray-700">
          Enter your natural language query:
        </label>
        <input
          type="text"
          id="nl-input"
          name="nl-input"
          className="border border-gray-300 rounded-md p-2 w-96 mb-4"
          placeholder="e.g., Show me all employees hired after 2020"
        />
        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600"
        >
          Send
        </button>
      </form>
    </div>
  );
}
