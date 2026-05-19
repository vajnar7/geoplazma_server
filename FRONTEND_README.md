# GeoPlazma Frontend - jQuery Application

## Overview

This is a modern web frontend for the GeoPlazma geospatial survey management system. It provides an intuitive interface for managing survey areas, visualizing GPS data on interactive maps, and controlling GNSS/NTRIP operations.

## Features

### ✨ Core Features
- **User Authentication**: Secure login/logout system with token-based authentication
- **Area Management**: Create, view, edit, and delete survey areas
- **Interactive Map**: Visualize geospatial points using Leaflet.js maps
- **Data Visualization**: Display GPS coordinates, timestamps, and coordinate ranges
- **NTRIP Control**: Start/stop NTRIP client operations
- **Data Export**: Export areas in multiple formats (GeoJSON, KML, CSV)

### 📱 User Interface
- Responsive design that works on desktop and mobile devices
- Sidebar navigation for easy area selection
- Real-time map updates when switching between areas
- Loading indicators and notifications for user feedback
- Modal dialogs for area creation and editing

## Technology Stack

- **Frontend Framework**: jQuery 3.6.0
- **Mapping Library**: Leaflet.js 1.9.4
- **Styling**: Custom CSS3 with responsive design
- **Backend Communication**: AJAX with JSON
- **Data Format**: GeoJSON, KML, CSV export support

## Installation & Setup

### Prerequisites
- Python 3.8+
- Django 3.1+
- All packages from `requirements.txt`

### Installation Steps

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install django-cors-headers
   ```

2. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

3. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

4. **Start Development Server**
   ```bash
   python manage.py runserver
   ```

5. **Access the Application**
   - Open browser to `http://localhost:8000`
   - Login with your email address

## API Endpoints

### Authentication
- `POST /api/login/` - User login
- `POST /api/logout/` - User logout

### Areas Management
- `GET /api/areas/` - Get all user areas
- `POST /api/areas/` - Create new area
- `DELETE /api/areas/` - Delete area

### GNSS/NTRIP Operations
- `POST /api/ntrip/` - Start/stop NTRIP client
- `POST /api/logfile/` - Upload and process log file

## Architecture

### JavaScript Modules

#### `api.js` - API Client
Handles all HTTP communication with the backend. Features:
- RESTful API wrapper with jQuery AJAX
- Token-based authentication
- Error handling and retry logic
- Request timeout management

#### `map.js` - Map Manager
Manages the Leaflet map and geospatial visualizations:
- Map initialization and controls
- Point markers and polylines
- Area bounds fitting
- Data export functions (GeoJSON, KML)
- Coordinate statistics calculation

#### `ui.js` - UI Manager
Handles user interface interactions:
- Section visibility toggling
- Loading overlays and spinners
- Notification toasts
- Modal dialogs
- Form error display
- Data export functions

#### `app.js` - Application Controller
Main application logic:
- Application state management
- Event listener setup
- Authentication flow
- Area CRUD operations
- NTRIP control
- User interactions orchestration

## File Structure

```
geoplazma_server/
├── templates/
│   └── index.html              # Main application template
├── static/
│   ├── css/
│   │   └── style.css           # Application styling
│   └── js/
│       ├── api.js              # API client
│       ├── map.js              # Map manager
│       ├── ui.js               # UI manager
│       └── app.js              # Main application
├── areas/
│   ├── models.py               # Data models (optimized)
│   ├── rest.py                 # REST API endpoints (optimized)
│   ├── views.py                # Django views
│   ├── urls.py                 # URL routing
│   └── ...
├── requirements.txt            # Python dependencies
└── manage.py                   # Django management
```

## Usage Guide

### Logging In
1. Click the email input field
2. Enter your registered email address
3. Click "Login" button
4. If successful, dashboard loads with your areas

### Creating a Survey Area
1. Click "+ Create Area" button in the sidebar
2. Enter area name and description
3. Enter geospatial points in JSON format:
   ```json
   [
     {"timestamp": 1234567890, "lon": 13.234, "lat": 46.123},
     {"timestamp": 1234567891, "lon": 13.235, "lat": 46.124}
   ]
   ```
4. Click "Save Area"

### Viewing Area on Map
1. Click on an area in the sidebar
2. Map automatically centers on the area
3. All GPS points displayed as markers
4. Coordinate range shown in details panel

### Exporting Data
1. Select an area
2. Click "Export" button
3. Choose format: GeoJSON, KML, or CSV
4. File downloads automatically

### NTRIP Control
1. Click "Start NTRIP" to begin NTRIP client
2. Click "Stop NTRIP" to halt client operations
3. Status notifications confirm operations

## Keyboard Shortcuts

- `Ctrl+N` - Create new area (when logged in)
- `ESC` - Close modal dialogs

## Code Optimizations

### Backend Optimizations
1. **Database Query Optimization**
   - Used `prefetch_related()` for areas with geopoints
   - Used `select_related()` for foreign key lookups
   - Reduced N+1 queries significantly

2. **API Response Efficiency**
   - Implemented caching for area queries
   - Used serializers for consistent response format
   - Bulk create for multiple geopoints

3. **Error Handling**
   - Comprehensive error messages
   - Proper HTTP status codes
   - Input validation on all endpoints

4. **Performance**
   - In-memory caching with 5-minute TTL
   - Connection pooling for database
   - Static file compression ready

### Frontend Optimizations
1. **Module Pattern**: Encapsulated code in IIFE modules
2. **Event Delegation**: Efficient event listener setup
3. **DOM Caching**: Cached jQuery selectors
4. **AJAX Optimization**: Proper error handling and timeouts
5. **Memory Management**: Proper cleanup of map layers

## Configuration

### Environment Variables
Set these in `settings.py`:
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Add your domain
- `DATABASES`: Configure your database
- `SECRET_KEY`: Use environment variable in production

### CORS Settings
Update `CORS_ALLOWED_ORIGINS` in `settings.py` for your domain:
```python
CORS_ALLOWED_ORIGINS = [
    "http://yourdoman.com",
    "https://yourdomain.com",
]
```

### Caching
Default uses in-memory cache. For production, use Redis:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## Performance Tips

1. **Reduce Point Count**: Large datasets can slow map rendering
2. **Use Pagination**: Implement pagination for large area lists
3. **Cache Aggressively**: Increase CACHE_TIMEOUT for stable data
4. **CDN for Static Files**: Serve CSS/JS from CDN in production
5. **Database Indexing**: Ensure proper indexes on frequently queried fields

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Login Issues
- Check email format
- Verify user exists in database
- Check browser console for errors

### Map Not Loading
- Verify Leaflet CDN is accessible
- Check browser console for 404 errors
- Ensure map container has size (300px minimum)

### AJAX Errors
- Check CORS configuration
- Verify API endpoints are correct
- Check authentication token validity

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check `STATIC_URL` and `STATIC_ROOT` settings
- Verify files exist in `static/` directory

## Development

### Adding New Features
1. Add API endpoint in `rest.py`
2. Update `api.js` with new API method
3. Add UI components in `index.html`
4. Implement logic in `app.js`
5. Style in `style.css`

### Debugging
- Use browser DevTools (F12)
- Check Django development server logs
- Use `console.log()` for JavaScript debugging
- Use Django shell for database queries

## Security Notes

- Never commit `SECRET_KEY` to version control
- Always use HTTPS in production
- Validate all input on backend
- Keep dependencies updated
- Use environment variables for sensitive data

## License

This project is part of the GeoPlazma system. All rights reserved.

## Support

For issues or questions, contact the development team.

---

**Last Updated**: 2026-05-11
**Version**: 1.0.0
