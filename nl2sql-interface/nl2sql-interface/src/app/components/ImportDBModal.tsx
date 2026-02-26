'use client';
import axios from "axios";
import { useState } from "react";
import { useRouter } from "next/navigation";

interface ImportDBModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ImportDBModal({ isOpen, onClose }: ImportDBModalProps) {
  const [dbType, setDbType] = useState("postgresql");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  if (!isOpen) return null;

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    
    const formData = new FormData(event.currentTarget);
    const dbURL = formData.get("db-url") as string;

    try {
      const response = await axios.post("http://127.0.0.1:8000/dbimport", {
        database_url: dbURL,
        database_type: dbType
      });
      
      const { session_id, conversation_id } = response.data;
      console.log("Database imported:", { session_id, conversation_id });
      
      // Navigate to the new conversation
      router.push(`/conversations/${conversation_id}`);
      onClose();
    } catch (error) {
      console.error("Error importing database:", error);
      alert("Failed to import database. Please check the URL and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-xl shadow-2xl p-8 max-w-lg w-full mx-4 border border-gray-800">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Import Database</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl leading-none"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Database Type
          </label>
          <select
            className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={dbType}
            onChange={(e) => setDbType(e.target.value)}
          >
            <option value="postgresql">PostgreSQL</option>
            <option value="mysql">MySQL</option>
            <option value="sqlite">SQLite</option>
            <option value="mssql">SQL Server</option>
          </select>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="db-url" className="block text-sm font-medium text-gray-300 mb-2">
              Connection String
            </label>
            <input
              type="text"
              id="db-url"
              name="db-url"
              placeholder={
                dbType === "sqlite"
                  ? "sqlite:///path/to/database.db"
                  : dbType === "postgresql"
                  ? "postgresql://user:password@host:port/dbname"
                  : dbType === "mysql"
                  ? "mysql://user:password@host:port/dbname"
                  : "mssql://user:password@host:port/dbname"
              }
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={loading}
            />
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Importing...' : 'Start Chat'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
