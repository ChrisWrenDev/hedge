const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Item {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export async function fetchItems(): Promise<Item[]> {
  const res = await fetch(`${API_BASE}/api/items`);
  if (!res.ok) throw new Error("Failed to fetch items");
  return res.json();
}

export async function createItem(data: {
  name: string;
  description?: string;
}): Promise<Item> {
  const res = await fetch(`${API_BASE}/api/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create item");
  return res.json();
}

export async function deleteItem(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/items/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete item");
}
