/**
 * GeoPlazma API Client
 * Handles all communication with the backend REST API
 */

const GeoPlazmaAPI = (function() {
    'use strict';

    // Configuration
    const config = {
        baseURL: window.location.protocol + '//' + window.location.host + '/api',
        token: localStorage.getItem('authToken') || '',
        timeout: 30000
    };

    // Helper function for API requests
    function apiRequest(method, endpoint, data = null, showLoading = true) {
        const url = config.baseURL + endpoint;
        const headers = {
            'Content-Type': 'application/json',
        };

        // Add token if available
        if (config.token) {
            headers['Authorization'] = 'Token ' + config.token;
        }

        const options = {
            type: method,
            url: url,
            headers: headers,
            timeout: config.timeout,
            dataType: 'json'
        };

        if (data) {
            options.data = JSON.stringify(data);
        }

        if (showLoading) {
            UI.showLoading();
        }

        return $.ajax(options)
            .always(function() {
                if (showLoading) {
                    UI.hideLoading();
                }
            });
    }

    // Public API
    return {
        // Set authentication token
        setToken: function(token) {
            config.token = token;
            localStorage.setItem('authToken', token);
        },

        // Get stored token
        getToken: function() {
            return config.token;
        },

        // Clear token
        clearToken: function() {
            config.token = '';
            localStorage.removeItem('authToken');
        },

        /**
         * User Management
         */

        login: function(email) {
            return apiRequest('POST', '/login/', { user: email });
        },

        logout: function(email) {
            return apiRequest('POST', '/logout/', { user: email });
        },

        checkStatus: function(email) {
            // Let apiRequest handle adding user email from localStorage
            return apiRequest('GET', '/status/', null, false);
        },

        /**
         * Areas Management
         */

        // Get all areas for current user
        getAreas: function() {
            return apiRequest('GET', '/areas/', null, true);
        },

        // Create new area with geospatial points
        createArea: function(areaData) {
            return apiRequest('POST', '/areas/', areaData, true);
        },

        // Delete an area
        deleteArea: function(areaName) {
            return apiRequest('DELETE', '/areas/', { name: areaName }, true);
        },

        /**
         * GNSS/NTRIP Operations
         */

        // Start NTRIP client
        startNTRIP: function() {
            return apiRequest('POST', '/ntrip/', { params: 'START' }, true);
        },

        // Stop NTRIP client
        stopNTRIP: function() {
            return apiRequest('POST', '/ntrip/', { params: 'STOP' }, true);
        },

        /**
         * Log File Operations
         */

        // Upload and process log file
        uploadLogFile: function(logData) {
            return apiRequest('POST', '/logfile/', { data: logData }, true);
        }
    };
})();

// Export for use in other modules
window.GeoPlazmaAPI = GeoPlazmaAPI;
