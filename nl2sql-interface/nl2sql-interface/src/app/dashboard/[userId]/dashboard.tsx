'use client';
import { useState } from "react";
import Sidebar from "../../components/Sidebar";
import ImportDBModal from "../../components/ImportDBModal";
import { useRouter } from "next/navigation";

export default function Dashboard() {
  const [showImportModal, setShowImportModal] = useState(false);
  const [showOptionsMenu, setShowOptionsMenu] = useState(false);
  const router = useRouter();
  const token = localStorage.getItem("token");
  // Extract user_id from the URL
  const pathname = window.location.pathname;
  const user_id = pathname.split("/")[2]; // Assuming URL is /dashboard/{user_id}

  if (!token) {
    // If no token is found, redirect to login page
    router.push("/auth/login");
    return null; // Render nothing while redirecting
  }

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <Sidebar user_id={user_id} onNewChat={() => setShowImportModal(true)} />

      {/*Profile Icon */}
      <div className="relative">
        <button
          onClick={() => setShowOptionsMenu(!showOptionsMenu)}
          className="absolute top-4 right-4 bg-gray-800 rounded-full p-2 focus:outline-none"
        >
          <svg
            className="w-6 h-6 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>

        {/* Options Menu */}
        {showOptionsMenu && (
          <div className="absolute top-12 right-4 bg-gray-800 rounded-lg shadow-lg py-2 w-48 z-10">
            <button
              onClick={() => {
                localStorage.removeItem("token");
                router.push("/auth/login");
              }}
              className="w-full text-left px-4 py-2 text-sm text-gray-400 hover:bg-gray-700 hover:text-white rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        )}
      </div>
      
      {/* Main Content - Welcome Screen */}
      <main className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="max-w-2xl text-center">
          <h1 className="text-5xl font-bold mb-6 text-white">
            Welcome to NL2SQL
          </h1>
          <p className="text-xl text-gray-400 mb-8">
            Transform natural language into SQL queries with AI
          </p>
          
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-4 text-white">Get Started</h2>
            <p className="text-gray-400 mb-6">
              Import a database to start a new conversation. Ask questions in plain English
              and get SQL queries generated automatically.
            </p>
            <button
              onClick={() => setShowImportModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors text-lg"
            >
              Import Database
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="text-3xl mb-2">💬</div>
              <h3 className="font-semibold text-white mb-2">Natural Language</h3>
              <p className="text-sm text-gray-400">
                Ask questions in plain English, no SQL knowledge required
              </p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="text-3xl mb-2">🔄</div>
              <h3 className="font-semibold text-white mb-2">Smart Retry</h3>
              <p className="text-sm text-gray-400">
                Refine queries automatically when results aren't what you expect
              </p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <div className="text-3xl mb-2">💾</div>
              <h3 className="font-semibold text-white mb-2">Conversations</h3>
              <p className="text-sm text-gray-400">
                All your queries saved per database connection
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Import Database Modal */}
      <ImportDBModal isOpen={showImportModal} onClose={() => setShowImportModal(false)} />
    </div>
  );
}
