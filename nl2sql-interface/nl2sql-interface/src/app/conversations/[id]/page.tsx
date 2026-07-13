'use client';
import { useState, useEffect, use } from "react";
import axios from "axios";
import Sidebar from "@/app/components/Sidebar";
import MessageBubble from "../../components/MessageBubble";
import ResultTable from "../../components/ResultTable";
import ImportDBModal from "@/app/components/ImportDBModal";
import { useRouter } from "next/navigation";

interface Message {
  id: string;
  message: string;
  isUser: boolean;
  result?: any[];
  generatedSQL?: string;
  userQuestion?: string;
}

function generateRetryPrompt(originalNL: string, failedQuery: string, errorMessage: string) {
  const aliasHint = /alias|table|column|no such column|no such table/i.test(errorMessage)
    ? "\nImportant: the failure is likely caused by a wrong table or alias choice. Re-evaluate the FROM/JOIN clauses and define every alias from the correct table before using it."
    : "";

  return `I tried to answer: "${originalNL}"
The previous SQL was:
${failedQuery}

The database returned this error:
${errorMessage}

Rewrite the SQL from scratch. Do NOT copy or lightly edit the previous query.\n\nRequirements:\n- Produce a brand new SQL query only.\n- Fix any wrong table names, aliases, joins, or column references.\n- If an alias is used, define it from the correct table first and use it consistently.\n- If the previous query used the wrong table, replace it with the correct one rather than reusing it.${aliasHint}\n\nReturn only the corrected SQL query.`;
}

export default function ConversationPage(props: {
  params: Promise<{ id: string }>
}) {
  const params = use(props.params);
  const conversationId = params.id as string;
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [currentNLInput, setCurrentNLInput] = useState<string>("");
  const [showRetryOption, setShowRetryOption] = useState(false);
  const [showRetryEditor, setShowRetryEditor] = useState(false);
  const [retryPrompt, setRetryPrompt] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showImportModal, setShowImportModal] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [showOptionsMenu, setShowOptionsMenu] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUserId = localStorage.getItem("user_id");
    setUserId(storedUserId);
    if (!token) {
      // If no token is found, redirect to login page
      router.push("/auth/login");
    }
  }, []);

  // Load conversation history on mount
  useEffect(() => {
    const loadConversation = async () => {
      try {
        const response = await axios.get(`http://127.0.0.1:8000/conversations/${conversationId}`);
        const history = response.data.messages || [];

        // Convert backend message format to frontend format
        const formattedMessages: Message[] = history.flatMap((msg: any) => {
          const msgs: Message[] = [];
          if (msg.user_message) {
            msgs.push({ id: crypto.randomUUID(), message: msg.user_message, isUser: true });
          }
          if (msg.assistant_response) {
            msgs.push({
              id: crypto.randomUUID(),
              message: msg.assistant_response,
              isUser: false,
              // Include cached results if available
              result: msg.cached_result,
              generatedSQL: msg.generated_sql,
              userQuestion: msg.user_message
            });
          }
          return msgs;
        });

        setMessages(formattedMessages);
        setSessionId(response.data.session_id);
      } catch (error) {
        console.error("Error loading conversation:", error);
      }
    };

    loadConversation();
  }, [conversationId]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const nlInput = formData.get("nl-input") as string;
    setThinking(true);
    if (!nlInput.trim()) return;
    
    // Reset form immediately before async operations
    form.reset();
    
    console.log("Natural Language Input:", nlInput);
    setMessages(prevMessages => [...prevMessages, { id: crypto.randomUUID(), message: nlInput, isUser: true }]);
    setCurrentNLInput(nlInput);
    setShowRetryOption(false);
    setShowRetryEditor(false);
    
    const sendMessage = async (message: string, originalUserQuestion: string) => {
      if (!sessionId) {
        alert("Session not found. Please reload the page.");
        return;
      }
      try {
        const response = await axios.post("http://127.0.0.1:8000/nlinput", {
          nl_input: message,
          session_id: sessionId
        });
        console.log("Response from backend:", response.data);
        const AIMessage = response.data.response;
        const generatedQuery = response.data.query;
        const assistantMessageId = crypto.randomUUID();
        setMessages(prevMessages => {
          return [
            ...prevMessages,
            {
              id: assistantMessageId,
              message: AIMessage,
              isUser: false,
              generatedSQL: generatedQuery,
              userQuestion: originalUserQuestion
            }
          ];
        });
        return { generatedQuery, assistantMessageId };
      } catch (error) {
        console.error("Error sending message:", error);
        setThinking(false);
        return null;
      }
    };

    const sendResult = await sendMessage(nlInput, nlInput);
    if (sendResult) {
      const { generatedQuery, assistantMessageId } = sendResult;
      setCurrentQuery(generatedQuery);
      const errorMsg = await executeQuery(generatedQuery, assistantMessageId, nlInput);
      if (errorMsg && errorMsg !== "Query executed successfully.") {
        const generatedRetryPrompt = generateRetryPrompt(nlInput, generatedQuery, errorMsg);
        setRetryPrompt(generatedRetryPrompt);
        setErrorMessage(errorMsg);
        setShowRetryEditor(true);
      }
      setThinking(false);
    }
  };

  const executeQuery = async (query: string, assistantMessageId: string, userQuestion: string) => {
    if (!sessionId) {
      alert("Session not found. Please reload the page.");
      return;
    }
    try {
      const response = await axios.post(`http://127.0.0.1:8000/executesql/${sessionId}`, {
        query: query
      });
      console.log("Query execution result:", response.data);
      console.log("Updating message id:", assistantMessageId);
      console.log("Result is array?", Array.isArray(response.data.result));

      if (response.data.error) {
        // Handle error response
        const errorMsg = response.data.error;
        setShowRetryEditor(true);
        setErrorMessage(errorMsg);
        return errorMsg;
      }

      if (Array.isArray(response.data.result)) {
        setMessages(prevMessages => {
          return prevMessages.map((msg) => {
            if (msg.id === assistantMessageId) {
              console.log("Found message to update with id:", msg.id);
              return {
                ...msg,
                result: response.data.result,
                generatedSQL: query,
                userQuestion
              };
            }
            return msg;
          });
        });
        setShowRetryOption(true);
        setErrorMessage(null);
      } else {
        const errorMsg = response.data.result || "Query executed successfully.";
        setMessages(prevMessages => [...prevMessages, {
          id: crypto.randomUUID(),
          message: typeof response.data.result === 'string'
            ? response.data.result
            : JSON.stringify(response.data.result),
          isUser: false
        }]);
        return errorMsg;
      }
    } catch (error: any) {
      console.error("Error executing query:", error);
      const errorMsg = error.response?.data?.error || error.message || "Unknown error executing query";
      return errorMsg;
    } finally {
      setThinking(false);
    }

  };

  const retryGenerateQuery = async (editedPrompt: string) => {
    if (!sessionId) {
      alert("Session not found. Please reload the page.");
      return;
    }
    try {
      setShowRetryEditor(false);
      setThinking(true);
      setMessages(prevMessages => [...prevMessages, { id: crypto.randomUUID(), message: editedPrompt, isUser: true }]);

      const response = await axios.post("http://127.0.0.1:8000/nlinput", {
        nl_input: editedPrompt,
        session_id: sessionId
      });
      console.log("Retry response from backend:", response.data);
      const AIMessage = response.data.response;
      const newGeneratedQuery = response.data.query;
      const assistantMessageId = crypto.randomUUID();
      setMessages(prevMessages => {
        return [
          ...prevMessages,
          {
            id: assistantMessageId,
            message: AIMessage,
            isUser: false,
            generatedSQL: newGeneratedQuery,
            userQuestion: editedPrompt
          }
        ];
      });

      setCurrentQuery(newGeneratedQuery);
      const queryResult = await executeQuery(newGeneratedQuery, assistantMessageId, editedPrompt);
      if (queryResult && queryResult !== "Query executed successfully.") {
        const generatedRetryPrompt = generateRetryPrompt(editedPrompt, newGeneratedQuery, queryResult);
        setRetryPrompt(generatedRetryPrompt);
        setErrorMessage(queryResult);
        setShowRetryEditor(true);
      } else {
      setShowRetryEditor(false);
      setRetryPrompt("");
      }
    } catch (error) {
      console.error("Error retrying query generation:", error);
    } finally {
      setThinking(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <Sidebar user_id={userId} onNewChat={() => {
        setShowImportModal(true);
      }} />

      {/*Profile Icon */}
      <div className="relative">
        <button
          onClick={() => setShowOptionsMenu(!showOptionsMenu)}
          className="absolute bottom-4 left-4 bg-gray-800 rounded-full p-2 focus:outline-none"
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
          <div className="absolute bottom-12 left-4 bg-gray-800 rounded-lg shadow-lg py-2 w-48 z-10">
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
      
      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((msg) => (
              <div key={msg.id} className="space-y-3">

                <MessageBubble message={msg.message} isUser={msg.isUser} />
                {msg.result && (
                  <div className="w-full">
                    <h2 className="text-xl font-semibold mb-3 text-white">Query Results:</h2>
                    <ResultTable
                      result={msg.result}
                      conversation_id={conversationId}
                      userQuestion={msg.userQuestion || ""}
                      generatedSQL={msg.generatedSQL || ""}
                    />
                  </div>
                )}
              </div>
            ))}

            {thinking && (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mr-2"></div>
                    <span className="text-gray-300">Thinking...</span>
                  </div>
                )}
            
            {/* Retry Editor */}
            {showRetryEditor && (
              <div className="w-full bg-yellow-900 bg-opacity-30 border-2 border-yellow-600 rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-2 text-white">Query Error - Retry Prompt</h2>
                <div className="mb-4">
                  <p className="text-sm text-gray-300 mb-2"><strong>Error:</strong> {errorMessage}</p>
                  <p className="text-sm text-gray-300 mb-2"><strong>Failed Query:</strong></p>
                  <pre className="bg-gray-800 p-2 rounded text-xs overflow-x-auto text-gray-200">{currentQuery}</pre>
                </div>
                <label htmlFor="retry-prompt" className="block mb-2 text-sm font-medium text-gray-200">
                  Review and edit the retry prompt before sending:
                </label>
                <textarea
                  id="retry-prompt"
                  value={retryPrompt}
                  onChange={(e) => setRetryPrompt(e.target.value)}
                  className="w-full bg-gray-800 text-gray-100 border border-gray-600 rounded-md p-3 mb-4 font-mono text-sm"
                  rows={8}
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => retryGenerateQuery(retryPrompt)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
                  >
                    Send Retry Prompt
                  </button>
                  <button
                    onClick={() => {
                      setShowRetryEditor(false);
                      setRetryPrompt("");
                    }}
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
            
            {/* Retry Option for Successful Queries */}
            {showRetryOption && (!errorMessage || errorMessage === "Query executed successfully." || errorMessage === "") && (
              <div className="w-full bg-blue-900 bg-opacity-30 border border-blue-600 rounded-lg p-4">
                <p className="text-gray-200 mb-3">Is the result not what you expected?</p>
                <button
                  onClick={() => {
                    const generatedRetryPrompt = generateRetryPrompt(
                      currentNLInput, 
                      currentQuery, 
                      "The query executed successfully but did not return the expected results."
                    );
                    setRetryPrompt(generatedRetryPrompt);
                    setShowRetryEditor(true);
                    setShowRetryOption(false);
                  }}
                  className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-md transition-colors"
                >
                  Revise Query
                </button>
              </div>
            )}
          </div>
        </div>
        
        {/* Input Area */}
        <div className="border-t border-gray-800 p-6 bg-gray-900">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <input
                type="text"
                id="nl-input"
                name="nl-input"
                className="flex-1 bg-gray-800 text-gray-100 border border-gray-700 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ask a question about your database..."
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                Send
              </button>
            </div>
          </form>
        </div>
        {/* Import Database Modal */}
        <ImportDBModal isOpen={showImportModal} onClose={() => setShowImportModal(false)} />
      </main>
    </div>
  );
}
