"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { fetchItems, createItem, deleteItem, type Item } from "@/lib/api";

export default function Dashboard() {
  const [items, setItems] = useState<Item[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await fetchItems();
      setItems(data);
    } catch {
      console.error("Could not reach API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await createItem({ name, description: description || undefined });
    setName("");
    setDescription("");
    load();
  };

  const handleDelete = async (id: string) => {
    await deleteItem(id);
    load();
  };

  const chartData = items.map((item) => ({
    name: item.name,
    chars: item.description?.length || 0,
  }));

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "1.5rem" }}>
        Hedge Dashboard
      </h1>

      <form
        onSubmit={handleCreate}
        style={{ display: "flex", gap: 8, marginBottom: 24 }}
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name"
          required
          style={{
            padding: "6px 10px",
            background: "#1a1a1a",
            border: "1px solid #333",
            color: "#fff",
            borderRadius: 4,
            flex: 1,
          }}
        />
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description"
          style={{
            padding: "6px 10px",
            background: "#1a1a1a",
            border: "1px solid #333",
            color: "#fff",
            borderRadius: 4,
            flex: 2,
          }}
        />
        <button
          type="submit"
          style={{
            padding: "6px 16px",
            background: "#3b82f6",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            cursor: "pointer",
          }}
        >
          Add
        </button>
      </form>

      {loading ? (
        <p>Loading...</p>
      ) : items.length === 0 ? (
        <p style={{ color: "#888" }}>No items yet.</p>
      ) : (
        <>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              marginBottom: 32,
            }}
          >
            <thead>
              <tr style={{ borderBottom: "1px solid #333", textAlign: "left" }}>
                <th style={{ padding: "8px 4px" }}>Name</th>
                <th style={{ padding: "8px 4px" }}>Description</th>
                <th style={{ padding: "8px 4px" }}>Created</th>
                <th style={{ padding: "8px 4px" }}></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} style={{ borderBottom: "1px solid #222" }}>
                  <td style={{ padding: "8px 4px" }}>{item.name}</td>
                  <td style={{ padding: "8px 4px", color: "#aaa" }}>
                    {item.description || "—"}
                  </td>
                  <td style={{ padding: "8px 4px", color: "#aaa" }}>
                    {new Date(item.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: "8px 4px" }}>
                    <button
                      onClick={() => handleDelete(item.id)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#ef4444",
                        cursor: "pointer",
                      }}
                    >
                      delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2 style={{ fontSize: "1rem", marginBottom: 12 }}>
            Description Length
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="name" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip
                contentStyle={{ background: "#1a1a1a", border: "1px solid #333" }}
              />
              <Bar dataKey="chars" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </>
      )}
    </main>
  );
}
