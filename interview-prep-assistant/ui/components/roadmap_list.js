function renderRoadmap(roadmapData) {
    const container = document.getElementById('roadmap-container');
    if (!container) return;
    
    let html = '<h3>Your Study Plan</h3>';
    if (roadmapData.weak_areas.length > 0) {
        html += `<p><strong>Focus Areas:</strong> ${roadmapData.weak_areas.join(', ')}</p>`;
    }
    
    html += '<ul style="list-style-type: none; padding: 0;">';
    
    roadmapData.roadmap.forEach(item => {
        let color = '#4caf50'; // green
        if (item.day <= 2) color = '#f44336'; // red
        else if (item.day <= 5) color = '#ff9800'; // amber
        
        html += `
            <li style="margin-bottom: 10px; padding: 10px; border-left: 4px solid ${color}; background: #f9f9f9; color: #333;">
                <strong>Day ${item.day} — ${item.topic}</strong> (${item.estimated_minutes} min)<br/>
                ${item.action}
            </li>
        `;
    });
    
    html += '</ul>';
    container.innerHTML = html;
}
