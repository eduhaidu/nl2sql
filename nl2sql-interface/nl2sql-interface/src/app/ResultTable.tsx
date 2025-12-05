'use client-side rendering';

export default function ResultTable({result}: {result: any[]}){
    if (result.length === 0 || (result.length === 1 && Object.keys(result[0]).length === 0)) {
        return <div className="text-white">No results to display.</div>;
    }

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
        </div>
    )
}