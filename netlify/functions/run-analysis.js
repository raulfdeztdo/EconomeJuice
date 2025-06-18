const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

exports.handler = async (event, context) => {
  // Solo permitir métodos POST
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
      },
      body: JSON.stringify({ error: 'Método no permitido' })
    };
  }

  // Manejar preflight CORS
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS'
      },
      body: ''
    };
  }

  try {
    console.log('Iniciando análisis manual desde función Netlify');
    
    // Detectar el directorio del proyecto
    let projectRoot = process.cwd();
    
    // En Netlify Functions, intentar diferentes rutas
    const possibleRoots = [
      '/opt/build/repo',
      process.cwd(),
      path.join(process.cwd(), '..', '..'),
      '/var/task'
    ];
    
    // Buscar el directorio que contenga src/nasdaq_analyzer.py
    for (const root of possibleRoots) {
      const testPython = path.join(root, 'src', 'nasdaq_analyzer.py');
      if (fs.existsSync(testPython)) {
        projectRoot = root;
        console.log(`Proyecto encontrado en: ${projectRoot}`);
        break;
      }
    }
    
    const pythonScript = path.join(projectRoot, 'src', 'nasdaq_analyzer.py');
    
    // Verificar que el script de Python existe
    if (!fs.existsSync(pythonScript)) {
      console.error('Script de Python no encontrado');
      console.error('Rutas probadas:', possibleRoots.map(root => path.join(root, 'src', 'nasdaq_analyzer.py')));
      console.error('Directorio actual:', process.cwd());
      
      try {
        console.error('Contenido del directorio actual:', fs.readdirSync(process.cwd()));
      } catch (e) {
        console.error('No se pudo leer el directorio actual');
      }
      
      return {
        statusCode: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ 
          error: 'Script de análisis no encontrado',
          cwd: process.cwd(),
          tried_paths: possibleRoots.map(root => path.join(root, 'src', 'nasdaq_analyzer.py'))
        })
      };
    }

    // Crear directorios necesarios
    const dataDir = path.join(projectRoot, 'data');
    const publicDataDir = path.join(projectRoot, 'public', 'data');
    
    try {
      if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
      }
      if (!fs.existsSync(publicDataDir)) {
        fs.mkdirSync(publicDataDir, { recursive: true });
      }
    } catch (dirError) {
      console.error('Error creando directorios:', dirError);
    }

    // Ejecutar el análisis directamente con Python
    return new Promise((resolve) => {
      // Intentar diferentes comandos de Python
      const pythonCommands = ['python3', 'python'];
      let pythonCmd = 'python3';
      
      // Verificar qué comando de Python está disponible
      exec('which python3', (error) => {
        if (error) {
          exec('which python', (error2) => {
            if (error2) {
              console.error('No se encontró Python instalado');
              pythonCmd = 'python3'; // Usar por defecto
            } else {
              pythonCmd = 'python';
            }
          });
        }
        
        console.log(`Ejecutando análisis con: ${pythonCmd}`);
        
        exec(`${pythonCmd} src/nasdaq_analyzer.py`, { 
          cwd: projectRoot,
          timeout: 300000, // 5 minutos timeout para Netlify
          env: { 
            ...process.env, 
            PATH: process.env.PATH + ':/usr/bin:/bin:/usr/local/bin',
            PYTHONPATH: projectRoot
          }
        }, (error, stdout, stderr) => {
          const timestamp = new Date().toISOString();
          
          if (error) {
            console.error('Error ejecutando análisis:', error);
            console.error('stderr:', stderr);
            console.error('stdout:', stdout);
            
            // Crear timestamp de error
            const errorTimestamp = {
              last_update: timestamp,
              status: 'error',
              message: `Error en actualización manual: ${error.message}`,
              details: stderr || error.message
            };
            
            // Escribir timestamp de error en ambas ubicaciones
            try {
              const errorPathData = path.join(dataDir, 'last_update.json');
              const errorPathPublic = path.join(publicDataDir, 'last_update.json');
              
              fs.writeFileSync(errorPathData, JSON.stringify(errorTimestamp, null, 2));
              fs.writeFileSync(errorPathPublic, JSON.stringify(errorTimestamp, null, 2));
              
              console.log('Timestamp de error guardado');
            } catch (writeError) {
              console.error('Error escribiendo timestamp de error:', writeError);
            }
            
            resolve({
              statusCode: 500,
              headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
              },
              body: JSON.stringify({ 
                error: 'Error ejecutando análisis',
                details: error.message,
                stderr: stderr,
                stdout: stdout
              })
            });
          } else {
            console.log('Análisis completado exitosamente');
            console.log('stdout:', stdout);
            
            // Crear timestamp de éxito
            const successTimestamp = {
              last_update: timestamp,
              status: 'success',
              message: 'Análisis ejecutado exitosamente desde Netlify Function'
            };
            
            try {
              // Copiar archivos JSON generados a public/data
              const files = fs.readdirSync(dataDir).filter(file => file.endsWith('.json'));
              
              for (const file of files) {
                const srcPath = path.join(dataDir, file);
                const destPath = path.join(publicDataDir, file);
                fs.copyFileSync(srcPath, destPath);
              }
              
              // Escribir timestamp de éxito
              const successPathData = path.join(dataDir, 'last_update.json');
              const successPathPublic = path.join(publicDataDir, 'last_update.json');
              
              fs.writeFileSync(successPathData, JSON.stringify(successTimestamp, null, 2));
              fs.writeFileSync(successPathPublic, JSON.stringify(successTimestamp, null, 2));
              
              console.log('Archivos copiados y timestamp actualizado');
            } catch (copyError) {
              console.error('Error copiando archivos:', copyError);
            }
            
            resolve({
              statusCode: 200,
              headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
              },
              body: JSON.stringify({ 
                success: true, 
                message: 'Análisis ejecutado exitosamente',
                output: stdout,
                timestamp: timestamp
              })
            });
          }
        });
      });
    });
    
  } catch (error) {
    console.error('Error en función Netlify:', error);
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ 
        error: 'Error interno del servidor',
        details: error.message 
      })
    };
  }
};