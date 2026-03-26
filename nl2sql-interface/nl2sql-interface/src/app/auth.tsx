'use client';
import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function Auth() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [showRegister, setShowRegister] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        const response = await axios.post("http://127.0.0.1:8000/login", { username, password });
        const token = response.data.token;
        localStorage.setItem("token", token);
        router.push("/dashboard");
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const response = await axios.post("http://127.0.0.1:8000/register", { username, password });
            const token = response.data.token;
            localStorage.setItem("token", token);
            router.push("/dashboard");
        } catch (error) {
            console.error("Registration failed:", error);
        }
    }

    return (
        <main className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="max-w-md w-full bg-gray-900 rounded-xl border border-gray-800 p-8">
                <h1 className="text-3xl font-bold mb-6 text-white text-center">
                    {showRegister ? "Create an Account" : "Login to NL2SQL"}
                </h1>
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full mb-4 px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {showRegister && (
                    <input
                        type="email"
                        placeholder="Email (optional)"
                        className="w-full mb-4 px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                )}
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full mb-6 px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                    onClick={showRegister ? handleRegister : handleLogin}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                    {showRegister ? "Register" : "Login"}
                </button>
                <p
                    onClick={() => setShowRegister(!showRegister)}
                    className="mt-4 text-sm text-gray-400 cursor-pointer text-center"
                >
                    {showRegister ? "Already have an account? Login" : "Don't have an account? Register"}
                </p>
            </div>
        </main>
    )
}