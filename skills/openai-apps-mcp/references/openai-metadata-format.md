# OpenAI Metadata Format Reference

## Complete List of OpenAI-Specific Annotations

### Tool Registration Metadata

```typescript
{
  name: 'tool_name',
  description: 'Use this when...',  // Action-oriented, critical for discovery
  inputSchema: { /* JSON Schema */ },
  annotations: {
    openai: {
      // REQUIRED for widgets
      outputTemplate: 'ui://widget/widget-name.html',

      // OPTIONAL status messages
      toolInvocation: {
        invoking: 'Loading...',      // Shown while tool executes
        invoked: 'Done!'              // Shown after completion
      },

      // OPTIONAL for read-only tools
      readOnlyHint: true  // Skips confirmation prompt
    }
  }
}
```

### Tool Response Metadata

```typescript
return {
  content: [{
    type: 'text',
    text: 'Response text shown in conversation'
  }],
  _meta: {
    // Data accessible via window.openai.getInitialData()
    initialData: {
      key: 'value',
      nested: {
        data: 'works too'
      }
    },

    // Optional: Control widget routing
    initialRoute: '/specific-view'
  },

  // Optional: Mark as error
  isError: false
};
```

### Resource Registration (Widgets)

```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [{
    uri: 'ui://widget/widget-name.html',  // MUST start with ui://widget/
    name: 'Human Readable Name',
    description: 'What this widget does',
    mimeType: 'text/html+skybridge'  // REQUIRED +skybridge suffix
  }]
}));
```

## Required Patterns

### 1. Resource URI Pattern

- **Format**: `ui://widget/{widget-name}.html`
- **Examples**:
  - ✅ `ui://widget/map.html`
  - ✅ `ui://widget/product-list.html`
  - ❌ `resource://map.html` (wrong prefix)
  - ❌ `/widgets/map.html` (no scheme)

### 2. MIME Type

- **Required**: `text/html+skybridge`
- **Why**: OpenAI uses the `+skybridge` suffix to identify renderable widgets
- **Standard `text/html` won't work** - widgets will display as plain text

### 3. Tool Descriptions

**Format**: Action-oriented, starts with "Use this when..."

**Good Examples**:
```typescript
'Use this when the user wants to see a map of a location'
'Use this when the user asks for weather forecast in a city'
'Use this when the user needs to search for products'
```

**Bad Examples**:
```typescript
'Shows a map'  // Too vague
'Weather tool'  // Not action-oriented
'Product search'  // Doesn't hint at usage
```

## window.openai API

Available in widget HTML:

```javascript
// Get data from tool handler
const data = window.openai.getInitialData();
// Returns the object from _meta.initialData

// Call another tool
window.openai.callTool({
  name: 'tool_name',
  arguments: {
    param: 'value'
  }
});

// Update widget state
window.openai.setWidgetState({ key: 'value' });

// Close widget
window.openai.close();
```

## Complete Example

```typescript
// Tool registration
mcpServer.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'show_restaurant_map',
    description: 'Use this when the user wants to see restaurant locations on a map',
    inputSchema: {
      type: 'object',
      properties: {
        city: { type: 'string', description: 'City name' },
        cuisine: { type: 'string', description: 'Type of cuisine', enum: ['italian', 'japanese', 'mexican'] }
      },
      required: ['city']
    },
    annotations: {
      openai: {
        outputTemplate: 'ui://widget/restaurant-map.html',
        toolInvocation: {
          invoking: 'Finding restaurants...',
          invoked: 'Here are the restaurants!'
        },
        readOnlyHint: true  // No confirmation needed
      }
    }
  }]
}));

// Tool handler
mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'show_restaurant_map') {
    const { city, cuisine } = request.params.arguments;

    // Fetch restaurant data
    const restaurants = await fetchRestaurants(city, cuisine);

    return {
      content: [{
        type: 'text',
        text: `Found ${restaurants.length} ${cuisine || ''} restaurants in ${city}`
      }],
      _meta: {
        initialData: {
          city,
          cuisine,
          restaurants: restaurants.map(r => ({
            id: r.id,
            name: r.name,
            lat: r.latitude,
            lng: r.longitude,
            rating: r.rating
          }))
        }
      }
    };
  }
});

// Resource registration
mcpServer.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [{
    uri: 'ui://widget/restaurant-map.html',
    name: 'Restaurant Map',
    description: 'Interactive map showing restaurant locations',
    mimeType: 'text/html+skybridge'
  }]
}));
```

```html
<!-- restaurant-map.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Restaurant Map</title>
  <style>
    body { font-family: system-ui; padding: 20px; }
    .restaurant { padding: 10px; border-bottom: 1px solid #ccc; }
  </style>
</head>
<body>
  <div id="map-container"></div>
  <div id="restaurants-list"></div>

  <script>
    if (window.openai && window.openai.getInitialData) {
      const data = window.openai.getInitialData();

      document.getElementById('map-container').innerHTML =
        `<h2>${data.cuisine || 'All'} Restaurants in ${data.city}</h2>`;

      const list = document.getElementById('restaurants-list');
      data.restaurants.forEach(restaurant => {
        const div = document.createElement('div');
        div.className = 'restaurant';
        div.innerHTML = `
          <strong>${restaurant.name}</strong>
          <span>⭐ ${restaurant.rating}</span>
        `;
        list.appendChild(div);
      });
    }
  </script>
</body>
</html>
```

## Checklist

- [ ] Resource URI starts with `ui://widget/`
- [ ] MIME type is `text/html+skybridge`
- [ ] Tool description is action-oriented
- [ ] `_meta.initialData` contains widget data
- [ ] Widget checks for `window.openai` before accessing
- [ ] Tool invocation messages provided (optional but recommended)
- [ ] `readOnlyHint: true` for read-only operations

---

**Reference**: OpenAI Apps SDK - https://developers.openai.com/apps-sdk
