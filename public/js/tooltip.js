// tooltip.js - handles custom tooltip for status badges

// This file sets up a lightweight tooltip that shows extra information stored in
// the `data-tooltip` attribute of elements with the class `status-badge`.
// It is loaded separately from `script.js` to keep the main file smaller and
// easier to maintain.
document.addEventListener('DOMContentLoaded', () => {
    // Create tooltip container
    const tooltip = document.createElement('div');
    tooltip.id = 'custom-tooltip';
    Object.assign(tooltip.style, {
        position: 'fixed',
        display: 'none',
        backgroundColor: 'white',
        color: 'black',
        padding: '8px 12px',
        borderRadius: '4px',
        boxShadow: '0 2px 5px rgba(0, 0, 0, 0.2)',
        border: '1px solid #ddd',
        zIndex: '9999',
        maxWidth: '300px',
        textAlign: 'center'
    });

    // Tooltip arrow
    const arrow = document.createElement('div');
    arrow.id = 'tooltip-arrow';
    Object.assign(arrow.style, {
        position: 'fixed',
        display: 'none',
        width: '0',
        height: '0',
        borderLeft: '8px solid transparent',
        borderRight: '8px solid transparent',
        borderTop: '8px solid white',
        zIndex: '9999'
    });

    document.body.appendChild(tooltip);
    document.body.appendChild(arrow);

    // Show tooltip
    document.body.addEventListener('mouseover', (e) => {
        const target = e.target.closest('.status-badge[data-tooltip]');
        if (!target) return;

        const tooltipText = target.getAttribute('data-tooltip');
        if (!tooltipText) return;

        tooltip.textContent = tooltipText;
        tooltip.style.display = 'block';
        arrow.style.display = 'block';

        const rect = target.getBoundingClientRect();
        const tooltipLeft = rect.left + rect.width / 2 - tooltip.offsetWidth / 2;
        const tooltipTop = rect.top - tooltip.offsetHeight - 10;

        tooltip.style.left = `${tooltipLeft}px`;
        tooltip.style.top = `${tooltipTop}px`;

        arrow.style.left = `${rect.left + rect.width / 2 - 8}px`;
        arrow.style.top = `${tooltipTop + tooltip.offsetHeight}px`;
    });

    // Hide tooltip
    document.body.addEventListener('mouseout', (e) => {
        const target = e.target.closest('.status-badge[data-tooltip]');
        if (!target) return;
        tooltip.style.display = 'none';
        arrow.style.display = 'none';
    });
});
