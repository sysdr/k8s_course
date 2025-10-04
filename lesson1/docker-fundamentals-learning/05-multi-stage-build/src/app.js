const express = require('express');
const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
    res.json({
        message: 'Multi-stage build demo',
        imageType: 'optimized',
        size: 'See docker images output'
    });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
