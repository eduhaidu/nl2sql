'use client-side rendering';

import { useState } from "react";
import axios from "axios";

interface Feedback {
    feedback_type: 'positive' | 'negative';
    user_question: string;
    generated_sql: string;
    corrected_sql?: string; // Optional, only needed for negative feedback
}

export default function ResultTable({result, conversation_id, userQuestion, generatedSQL}: {result: any[], conversation_id: string, userQuestion: string, generatedSQL: string}) {
    const [feedback, setFeedback] = useState<'none' | 'positive' | 'negative'>('none');
    // Safety check: ensure result is an array
    if (!Array.isArray(result)) {
        return <div className="text-white">Invalid result format.</div>;
    }
    
    if (result.length === 0 || (result.length === 1 && Object.keys(result[0]).length === 0)) {
        return <div className="text-white">No results to display.</div>;
    }

    const handleFeedback = (type: 'positive' | 'negative') => {
        setFeedback(type);
        // Send feedback to backend
        const feedbackData: Feedback = {
            feedback_type: type,
            user_question: userQuestion,
            generated_sql: generatedSQL
        };
        axios.post(`http://127.0.0.1:8000/feedback/${conversation_id}`, feedbackData)
            .then(response => {
                console.log("Feedback submitted:", response.data);
            })
            .catch(error => {
                console.error("Error submitting feedback:", error);
            });
    };

    const columns = Object.keys(result[0]);

    return (
        <div className="overflow-x-auto w-full">
            <table className="min-w-full bg-white border border-gray-300">
                <thead>
                    <tr>
                        {columns.map((col) => (
                            <th
                                key={col}
                                className="py-2 px-4 border-b border-gray-300 bg-gray-200 text-left text-sm font-semibold text-gray-700"
                            >
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {result.map((row, rowIndex) => (
                        <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                            {columns.map((col) => (
                                <td
                                    key={col}
                                    className="py-2 px-4 border-b border-gray-300 text-sm text-gray-900"
                                >
                                    {row[col] !== null && row[col] !== undefined ? row[col].toString() : 'NULL'}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            <div className="mt-4 flex space-x-2">
                <button onClick={() => handleFeedback('positive')} className={`px-4 py-2 rounded-lg text-white ${feedback === 'positive' ? 'bg-green-600' : 'bg-gray-600 hover:bg-gray-700'}`}>
                    👍
                </button>
                <button onClick={() => handleFeedback('negative')} className={`px-4 py-2 rounded-lg text-white ${feedback === 'negative' ? 'bg-red-600' : 'bg-gray-600 hover:bg-gray-700'}`}>
                    👎
                </button>
            </div>
        </div>
    )
}