const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Ruta para ejecutar análisis manual
app.post('/run-analysis', (req, res) => {
    console.log('Solicitud de análisis manual recibida');
    
    const scriptPath = path.join(__dirname, 'scripts', 'run_daily_analysis.sh');
    
    // Verificar que el script existe
    if (!fs.existsSync(scriptPath)) {
        console.error('Script no encontrado:', scriptPath);
        return res.status(500).json({ 
            error: 'Script de análisis no encontrado',
            path: scriptPath 
        });
    }
    
    // Ejecutar el script
    exec(`bash "${scriptPath}"`, { 
        cwd: __dirname,
        timeout: 120000 // 2 minutos timeout
    }, (error, stdout, stderr) => {
        if (error) {
            console.error('Error ejecutando análisis:', error);
            console.error('stderr:', stderr);
            
            // Crear un timestamp de error
            const errorTimestamp = {
                last_update: new Date().toISOString(),
                status: 'error',
                message: `Error en actualización manual: ${error.message}`
            };
            
            // Intentar escribir el timestamp de error
            try {
                fs.writeFileSync(
                    path.join(__dirname, 'data', 'last_update.json'),
                    JSON.stringify(errorTimestamp, null, 2)
                );
            } catch (writeError) {
                console.error('Error escribiendo timestamp de error:', writeError);
            }
            
            return res.status(500).json({ 
                error: 'Error ejecutando análisis',
                details: error.message,
                stderr: stderr
            });
        }
        
        console.log('Análisis completado exitosamente');
        console.log('stdout:', stdout);
        
        res.json({ 
            success: true, 
            message: 'Análisis ejecutado exitosamente',
            output: stdout
        });
    });
});

// Ruta para servir archivos de datos
app.get('/data/:filename', (req, res) => {
    const filename = req.params.filename;
    const filePath = path.join(__dirname, 'data', filename);
    
    if (fs.existsSync(filePath)) {
        res.sendFile(filePath);
    } else {
        res.status(404).json({ error: 'Archivo no encontrado' });
    }
});

// Ruta principal
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Iniciar servidor
app.listen(PORT, () => {
    console.log(`Servidor ejecutándose en http://localhost:${PORT}`);
    console.log('Rutas disponibles:');
    console.log('  GET  / - Dashboard principal');
    console.log('  POST /run-analysis - Ejecutar análisis manual');
    console.log('  GET  /data/:filename - Servir archivos de datos');
});

// Manejo de errores
process.on('uncaughtException', (error) => {
    console.error('Error no capturado:', error);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Promesa rechazada no manejada:', reason);
});