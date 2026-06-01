/**
 * GeoPlazma Main Application
 * Orchestrates all components and handles application flow
 */

$(document).ready(function() {
    'use strict';

    // Application State
    let appState = {
        currentUser: null,
        areas: [],
        selectedArea: null,
        isLoggedIn: false,
        mapInitialized: false
    };

    // ============================================
    // Initialization
    // ============================================

    function initApp() {
        setupEventListeners();
        checkAuthStatus();
    }

    function checkAuthStatus() {
        const email = localStorage.getItem('userEmail');

        if (!email) {
            showLoginView();
            return;
        }

        // Verify with backend that user is still logged in
        GeoPlazmaAPI.checkStatus(email)
            .done(function(response) {
                if (response.logged_in) {
                    appState.isLoggedIn = true;
                    appState.currentUser = email;
                    loadDashboard();
                } else {
                    // User email exists but logged_in is false
                    localStorage.removeItem('userEmail');
                    GeoPlazmaAPI.clearToken();
                    showLoginView();
                }
            })
            .fail(function() {
                // If status check fails, default to login view
                showLoginView();
            });
    }

    // ============================================
    // View Management
    // ============================================

    function showLoginView() {
        UI.showSection('#loginSection');
        appState.isLoggedIn = false;
        $('#logoutBtn').addClass('hidden');
    }

    function showDashboardView() {
        UI.showSection('#dashboardSection');
        appState.isLoggedIn = true;
        $('#logoutBtn').removeClass('hidden');
        // Initialize the map when dashboard becomes visible (only once)
        if (!appState.mapInitialized) {
            if (window.GeoPlazmaMap && typeof GeoPlazmaMap.init === 'function') {
                GeoPlazmaMap.init();
                appState.mapInitialized = true;
            }
        }

        // Ensure the Leaflet map resizes to fill the visible container
        if (window.GeoPlazmaMap && typeof GeoPlazmaMap.invalidateSize === 'function') {
            GeoPlazmaMap.invalidateSize();
        }
    }

    function loadDashboard() {
        UI.updateUserInfo(appState.currentUser);
        loadAreas();
    }

    // ============================================
    // Areas Management
    // ============================================

    function loadAreas() {
        UI.showLoading('Loading areas...');

        GeoPlazmaAPI.getAreas()
            .done(function(response) {
                const areas = response.response || [];
                appState.areas = areas;
                UI.renderAreasList(areas);
                UI.showNotification('Areas loaded successfully', 'success', 2000);

                if (areas.length > 0) {
                    selectArea(0);
                }
            })
            .fail(function(xhr) {
                handleError(xhr, 'Failed to load areas');
            })
            .always(function() {
                UI.hideLoading();
            });
    }

    function selectArea(index) {
        if (index < 0 || index >= appState.areas.length) {
            return;
        }

        appState.selectedArea = appState.areas[index];

        // Update UI
        $('.area-item').removeClass('active');
        $(`.area-item[data-area-index="${index}"]`).addClass('active');

        // Display on map and show details
        GeoPlazmaMap.displayArea(appState.selectedArea, index);
        UI.updateAreaDetails(appState.selectedArea);
    }

    function createArea(formData) {
        const areaName = formData.name.trim();
        let points = [];

        if (formData.pointsData.trim()) {
            try {
                points = JSON.parse(formData.pointsData);
                if (!Array.isArray(points)) {
                    throw new Error('Points must be an array');
                }
            } catch (e) {
                UI.showFormError('Invalid JSON format for points: ' + e.message);
                return;
            }
        }

        if (!areaName) {
            UI.showFormError('Area name is required');
            return;
        }

        const data = {
            name: areaName,
            points: points
        };

        UI.showLoading('Creating area...');

        GeoPlazmaAPI.createArea(data)
            .done(function(response) {
                UI.showNotification('Area created successfully', 'success');
                UI.hideModal('#areaModal');
                UI.clearModal();
                loadAreas();
            })
            .fail(function(xhr) {
                handleError(xhr, 'Failed to create area');
            })
            .always(function() {
                UI.hideLoading();
            });
    }

    function deleteArea(areaName) {
        if (!confirm(`Are you sure you want to delete "${areaName}"?\n\nThis action cannot be undone.`)) {
            return;
        }

        UI.showLoading('Deleting area...');

        GeoPlazmaAPI.deleteArea(areaName)
            .done(function(response) {
                UI.showNotification('Area deleted successfully', 'success');
                appState.selectedArea = null;
                loadAreas();
            })
            .fail(function(xhr) {
                handleError(xhr, 'Failed to delete area');
            })
            .always(function() {
                UI.hideLoading();
            });
    }

    // ============================================
    // NTRIP Operations
    // ============================================

    function startNTRIP() {
        UI.showLoading('Starting NTRIP client...');

        GeoPlazmaAPI.startNTRIP()
            .done(function(response) {
                UI.showNotification('NTRIP client started', 'success');
            })
            .fail(function(xhr) {
                handleError(xhr, 'Failed to start NTRIP client');
            })
            .always(function() {
                UI.hideLoading();
            });
    }

    function stopNTRIP() {
        UI.showLoading('Stopping NTRIP client...');

        GeoPlazmaAPI.stopNTRIP()
            .done(function(response) {
                UI.showNotification('NTRIP client stopped', 'success');
            })
            .fail(function(xhr) {
                handleError(xhr, 'Failed to stop NTRIP client');
            })
            .always(function() {
                UI.hideLoading();
            });
    }

    // ============================================
    // Authentication
    // ============================================

    function login(email) {
        email = email.trim();

        if (!email) {
            UI.showNotification('Please enter a valid email', 'error');
            return;
        }

        UI.showLoading('Logging in...');

        GeoPlazmaAPI.login(email)
            .done(function(response) {
                appState.currentUser = email;
                appState.isLoggedIn = true;

                // Store credentials
                localStorage.setItem('userEmail', email);

                UI.showNotification('Logged in successfully', 'success');
                showDashboardView();
                loadDashboard();
            })
            .fail(function(xhr) {
                handleError(xhr, 'Login failed');
            })
            .always(function() {
                UI.hideLoading();
            });
    }

    function logout() {
        // Safety check: only logout if actually logged in
        if (!appState.isLoggedIn || !appState.currentUser) {
            showLoginView();
            return;
        }

        if (!confirm('Are you sure you want to logout?')) {
            return;
        }

        const email = appState.currentUser;
        UI.showLoading('Logging out...');

        GeoPlazmaAPI.logout(email)
            .done(function(response) {
                appState.isLoggedIn = false;
                appState.currentUser = null;
                appState.areas = [];
                appState.selectedArea = null;

                // Clear storage
                localStorage.removeItem('authToken');
                localStorage.removeItem('userEmail');
                GeoPlazmaAPI.clearToken();

                UI.showNotification('Logged out successfully', 'success');
                showLoginView();
                GeoPlazmaMap.clearMap();
            })
            .fail(function(xhr) {
                handleError(xhr, 'Logout failed');
            })
            .always(function() {
                UI.hideLoading();
            });
    }

    // ============================================
    // Error Handling
    // ============================================

    function handleError(xhr, message) {
        let errorMsg = message;

        if (xhr.responseJSON && xhr.responseJSON.error) {
            errorMsg = xhr.responseJSON.error;
        } else if (xhr.status === 0) {
            errorMsg = 'Network error. Please check your connection.';
        } else if (xhr.status === 401) {
            errorMsg = 'Unauthorized. Please login again.';
            logout();
        } else if (xhr.status === 404) {
            errorMsg = 'Resource not found.';
        } else if (xhr.status === 500) {
            errorMsg = 'Server error. Please try again later.';
        }

        UI.showNotification(errorMsg, 'error', 5000);
        console.error('Error:', xhr);
    }

    // ============================================
    // Event Listeners
    // ============================================

    function setupEventListeners() {
        // Login Form
        $('#loginForm').on('submit', function(e) {
            e.preventDefault();
            const email = $('#emailInput').val();
            login(email);
        });

        // Logout Button
        $('#logoutBtn').on('click', function(e) {
            e.preventDefault();
            logout();
        });

        // Area List Selection
        $(document).on('click', '.area-item', function() {
            const index = $(this).attr('data-area-index');
            selectArea(parseInt(index));
        });

        // Create Area Button
        $('#createAreaBtn').on('click', function() {
            $('#areaModalTitle').text('Create New Area');
            UI.clearModal();
            UI.showModal('#areaModal');
        });

        // Edit Area Button
        $(document).on('click', '#editAreaBtn', function() {
            if (!appState.selectedArea) return;
            $('#areaModalTitle').text('Edit Area');
            $('#areaName').val(appState.selectedArea.name);
            UI.showModal('#areaModal');
        });

        // Delete Area Button
        $(document).on('click', '#deleteAreaBtn', function() {
            if (!appState.selectedArea) return;
            deleteArea(appState.selectedArea.name);
        });

        // Export Area Button
        $(document).on('click', '#exportAreaBtn', function() {
            if (!appState.selectedArea) return;

            const area = appState.selectedArea;
            const format = prompt('Export format:\n1. GeoJSON\n2. KML\n3. CSV\n\nEnter number (1-3):', '1');

            switch (format) {
                case '1':
                    UI.exportAreaAsGeoJSON(area);
                    break;
                case '2':
                    UI.exportAreaAsKML(area);
                    break;
                case '3':
                    UI.exportAreaAsCSV(area);
                    break;
                default:
                    UI.showNotification('Invalid format', 'error');
            }
        });

        // Area Form Submission
        $('#areaForm').on('submit', function(e) {
            e.preventDefault();
            const formData = {
                name: $('#areaName').val(),
                description: $('#areaDescription').val(),
                pointsData: $('#pointsData').val()
            };
            createArea(formData);
        });

        // NTRIP Buttons
        $('#startNTRIPBtn').on('click', function() {
            startNTRIP();
        });

        $('#stopNTRIPBtn').on('click', function() {
            stopNTRIP();
        });

        // Modal Close Button
        $('.close').on('click', function() {
            UI.hideModal('#areaModal');
        });

        // Modal Close on Outside Click
        $(window).on('click', function(e) {
            const $modal = $('#areaModal');
            if (e.target === $modal[0]) {
                UI.hideModal('#areaModal');
            }
        });

        // Keyboard Shortcuts
        $(document).on('keydown', function(e) {
            // ESC to close modal
            if (e.keyCode === 27) {
                UI.hideModal('#areaModal');
            }
            // Ctrl+N to create new area (when logged in)
            if (e.ctrlKey && e.keyCode === 78 && appState.isLoggedIn) {
                e.preventDefault();
                $('#createAreaBtn').click();
            }
        });
    }

    // ============================================
    // Application Start
    // ============================================

    initApp();
});
