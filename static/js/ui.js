/**
 * GeoPlazma UI Manager
 * Handles all UI interactions, dialogs, and notifications
 */

const UI = (function() {
    'use strict';

    // Hide/show sections
    function showSection(sectionId) {
        $('.section-login, .section-dashboard').addClass('hidden').removeClass('visible');
        $(sectionId).removeClass('hidden').addClass('visible');
    }

    // Loading overlay
    function showLoading(text = 'Loading...') {
        $('#loadingText').text(text);
        $('#loadingModal').removeClass('hidden').addClass('visible');
    }

    function hideLoading() {
        $('#loadingModal').removeClass('hidden').addClass('hidden');
    }

    // Notification toast
    function showNotification(message, type = 'success', duration = 3000) {
        const $notification = $('#notification');
        $notification
            .removeClass('hidden success error info')
            .addClass(type)
            .text(message)
            .removeClass('hidden')
            .addClass('visible');

        if (duration > 0) {
            setTimeout(() => {
                $notification.addClass('hidden').removeClass('visible');
            }, duration);
        }
    }

    // Modal functions
    function showModal(modalId) {
        $(modalId).removeClass('hidden').addClass('visible');
    }

    function hideModal(modalId) {
        $(modalId).removeClass('hidden').addClass('hidden');
    }

    function clearModal() {
        $('#areaForm')[0].reset();
        $('#areaFormError').addClass('hidden').text('');
    }

    // Area list rendering
    function renderAreasList(areas) {
        const $list = $('#areasList');
        $list.empty();

        if (!areas || areas.length === 0) {
            $list.html('<p class="text-muted">No areas yet</p>');
            return;
        }

        areas.forEach((area, index) => {
            const $item = $('<div>')
                .addClass('area-item')
                .attr('data-area-id', area.id)
                .attr('data-area-index', index)
                .html(`
                    <div style="font-weight: 500;">${escapeHtml(area.name)}</div>
                    <div style="font-size: 0.85rem; opacity: 0.7;">
                        ${area.points.length} point${area.points.length !== 1 ? 's' : ''}
                    </div>
                `);

            $list.append($item);
        });
    }

    // Update area details panel
    function updateAreaDetails(area) {
        const stats = GeoPlazmaMap.getAreaStats(area);

        $('#selectedAreaName').text(area.name);
        $('#pointsCount').text(stats.pointCount);
        $('#latRange').text(stats.latRange);
        $('#lonRange').text(stats.lonRange);

        $('#areaDetailsSection').removeClass('hidden').addClass('visible');
    }

    // Update user info display
    function updateUserInfo(email) {
        $('#userEmail').text(email);
    }

    // Show error in form
    function showFormError(message) {
        $('#areaFormError')
            .text(message)
            .removeClass('hidden');
    }

    // Helper to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Export data functions
    function downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    }

    function exportAreaAsGeoJSON(area) {
        const geojson = GeoPlazmaMap.exportAsGeoJSON(area);
        const filename = `${area.name.replace(/\s+/g, '_')}_${Date.now()}.geojson`;
        downloadFile(JSON.stringify(geojson, null, 2), filename, 'application/json');
    }

    function exportAreaAsKML(area) {
        const kml = GeoPlazmaMap.exportAsKML(area);
        const filename = `${area.name.replace(/\s+/g, '_')}_${Date.now()}.kml`;
        downloadFile(kml, filename, 'application/xml');
    }

    function exportAreaAsCSV(area) {
        let csv = 'Latitude,Longitude,Timestamp,Date\n';
        area.points.forEach(point => {
            const date = new Date(point.timestamp * 1000).toISOString();
            csv += `${point.lat},${point.lon},${point.timestamp},"${date}"\n`;
        });
        const filename = `${area.name.replace(/\s+/g, '_')}_${Date.now()}.csv`;
        downloadFile(csv, filename, 'text/csv');
    }

    // Public API
    return {
        showSection: showSection,
        showLoading: showLoading,
        hideLoading: hideLoading,
        showNotification: showNotification,
        showModal: showModal,
        hideModal: hideModal,
        clearModal: clearModal,
        renderAreasList: renderAreasList,
        updateAreaDetails: updateAreaDetails,
        updateUserInfo: updateUserInfo,
        showFormError: showFormError,
        escapeHtml: escapeHtml,
        downloadFile: downloadFile,
        exportAreaAsGeoJSON: exportAreaAsGeoJSON,
        exportAreaAsKML: exportAreaAsKML,
        exportAreaAsCSV: exportAreaAsCSV
    };
})();

// Export for use in other modules
window.UI = UI;
