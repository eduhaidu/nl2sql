'use client';
import axios from "axios";
import {useState} from "react";

interface ImportDBProps {
    setSessionId: (id: string | null) => void;
    currentSessionId: string | null;
}

export default function ImportDB({ setSessionId, currentSessionId }: ImportDBProps) {
    const [dbType, setDbType] = useState("postgresql");
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>)=>{
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        const dbURL = formData.get("db-url") as string;
        console.log("Database URL:", dbURL);

        const importDatabase = async (databaseUrl: string) => {
            try{
                // Cleanup old session if exists
                if (currentSessionId) {
                    try {
                        await axios.delete(`http://127.0.0.1:8000/disconnect/${currentSessionId}`);
                        console.log("Old session cleaned up");
                    } catch (error) {
                        console.warn("Failed to cleanup old session:", error);
                    }
                }
                
                // Create new session
                const response = await axios.post("http://127.0.0.1:8000/dbupdate", { 
                    database_url: databaseUrl 
                });
                const sessionId = response.data.session_id;
                console.log("Response from backend:", response.data);
                setSessionId(sessionId);
                alert("Database imported successfully!");
            } catch (error) {
                console.error("Error importing database:", error);
                alert("Failed to import database. Please try again.");
            }
        }
        await importDatabase(dbURL);
    };

    return (
        <div className="flex min-h-full flex-col items-center justify-between p-8 bg-gray-900 rounded-lg shadow-2xl">
            <h1 className="text-3xl font-bold mb-6 text-white">Import Database</h1>
            <div>
                <h2 className="text-md font-medium text-gray-300 mb-4">Select your database type:</h2>
                <select
                    className="bg-gray-800 border border-gray-600 text-white rounded-md p-2 w-64 mb-6 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={dbType}
                    onChange={(e) => setDbType(e.target.value)}
                >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                    <option value="sqlite">SQLite</option>
                    <option value="mssql">SQL Server</option>
                </select>
            </div>
            {dbType && (
                <form action="submit" className="flex flex-col items-start" onSubmit={handleSubmit}>
                    <label htmlFor="db-url" className="block mb-2 text-md font-medium text-gray-300">
                        Enter your {dbType} database URL:
                    </label>
                    <input
                        type="text"
                        id="db-url"
                        name="db-url"
                        placeholder={`e.g., ${dbType === "sqlite" ? "sqlite:///path/to/db.sqlite" : dbType === "postgresql" ? "postgresql://user:password@host:port/dbname" : dbType === "mysql" ? "mysql://user:password@host:port/dbname" : "mssql://user:password@host:port/dbname"}`}
                        className="bg-gray-800 border border-gray-600 text-white rounded-md p-2 w-96 mb-4 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                    <button
                        type="submit"
                        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                    >
                        Import Database
                    </button>
                </form>
            )}
        </div>
    );
}