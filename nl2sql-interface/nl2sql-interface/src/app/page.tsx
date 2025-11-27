'use client';
import axios from "axios";
import ImportDB from "./importdb";
import MessageBubble from "./MessageBubble";
import { useState, useEffect } from "react";

export default function Home() {
  const [messages, setMessages] = useState<{ message: string; isUser: boolean }[]>([]);
  const [showImportDB, setShowImportDB] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
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
        setMessages(prevMessages => [...prevMessages, { message: AIMessage, isUser: false }]);
      } catch (error) {
        console.error("Error sending message:", error);
      }
    }
    await sendMessage(nlInput);
    event.currentTarget.reset();
  };
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
