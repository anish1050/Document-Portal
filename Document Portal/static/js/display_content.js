function loadContent(text, images, tables, flowcharts) {
    
    document.getElementById('extracted-text').innerText = text;

    
    const imagesContainer = document.getElementById('images-container');
    images.forEach((image, index) => {
        const img = document.createElement('img');
        img.src = image;
        img.alt = `PDF page ${index + 1}`;
        imagesContainer.appendChild(img);
    });

    
    document.getElementById('extracted-tables').innerText = tables;

    
    document.getElementById('extracted-flowcharts').innerText = flowcharts;
}