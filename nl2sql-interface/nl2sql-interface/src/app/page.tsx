'use client';
import axios from "axios";

export default function Home() {
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>)=>{
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const nlInput = formData.get("nl-input") as string;
    console.log("Natural Language Input:", nlInput);
    
    const sendMessage = async (message: string) => {
      try{
        const response = await axios.post("http://127.0.0.1:8000/nlinput",{
          nl_input: message
        });
        console.log("Response from backend:", response.data);
      } catch (error) {
        console.error("Error sending message:", error);
      }
    }
    await sendMessage(nlInput);
  };
  return (
    <div className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold mb-8">Welcome to the NL2SQL Interface</h1>
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
