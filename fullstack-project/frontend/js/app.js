// API Configuration
// Use relative URL since frontend and backend are on the same origin
const API_BASE_URL = '';

// API Functions
async function fetchItems() {
    try {
        const response = await fetch(`${API_BASE_URL}/items`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching items:', error);
        throw error;
    }
}

async function fetchItemById(itemId) {
    try {
        const response = await fetch(`${API_BASE_URL}/items/${itemId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`Error fetching item ${itemId}:`, error);
        throw error;
    }
}

async function createItem(itemData) {
    try {
        const response = await fetch(`${API_BASE_URL}/items`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(itemData),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error creating item:', error);
        throw error;
    }
}

async function updateItem(itemId, itemData) {
    try {
        const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(itemData),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`Error updating item ${itemId}:`, error);
        throw error;
    }
}

async function deleteItem(itemId) {
    try {
        const response = await fetch(`${API_BASE_URL}/items/${itemId}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return true;
    } catch (error) {
        console.error(`Error deleting item ${itemId}:`, error);
        throw error;
    }
}

// Data Loading and Display Functions
async function loadItems() {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = 'block';
    }
    
    try {
        const items = await fetchItems();
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
        displayItems(items);
        return items;
    } catch (error) {
        console.error('Failed to load items:', error);
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
        displayError('Failed to load items. Please try again later.');
        return [];
    }
}

function displayItems(items) {
    const container = document.getElementById('items-container');
    if (!container) {
        console.warn('Items container not found');
        return;
    }

    if (items.length === 0) {
        container.innerHTML = '<p>No items found.</p>';
        return;
    }

    container.innerHTML = items.map(item => `
        <div class="item-card" data-item-id="${item.id}">
            <h3>${escapeHtml(item.title)}</h3>
            <p class="category">Category: ${escapeHtml(item.category)}</p>
            <div class="tags">
                ${item.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        </div>
    `).join('');
}

function displayError(message) {
    const container = document.getElementById('items-container');
    if (container) {
        container.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('App initialized');
    // Load items automatically on page load
    loadItems();
    
    // Set up auto-refresh (optional - reload data every 30 seconds)
    // setInterval(loadItems, 30000);
});

// Export functions for use in other scripts or console
window.appAPI = {
    fetchItems,
    fetchItemById,
    createItem,
    updateItem,
    deleteItem,
    loadItems,
    displayItems
};

