function renderPeerComparison(peerData) {
    const container = document.getElementById('peer-comparison-container');
    if (!container) return;
    
    if (peerData.insufficient_data) {
        container.innerHTML = '<p>Not enough data yet to compare.</p>';
        return;
    }
    
    let html = `<p><strong>You scored better than ${peerData.percentile}% of people who practiced this question.</strong></p>`;
    html += `<pre style="font-family: monospace; background: #2b2b2b; color: #fff; padding: 10px; border-radius: 5px;">`;
    
    // Create text bars
    const categories = ['clarity', 'depth', 'relevance', 'starFormat', 'roleFit'];
    categories.forEach(cat => {
        const val = peerData.avg_breakdown ? peerData.avg_breakdown[cat] : 0;
        const filled = Math.floor(val);
        const bar = '█'.repeat(filled) + '░'.repeat(10 - filled);
        const formattedCat = cat.padEnd(12, ' ');
        html += `${formattedCat} ${bar}  ${val.toFixed(1)}\n`;
    });
    
    html += `</pre>`;
    
    if (peerData.top_gap) {
        html += `<p style="color: #ff9800; font-size: 0.9em;">Your biggest gap vs peers is: ${peerData.top_gap}</p>`;
    }
    
    container.innerHTML = html;
}
