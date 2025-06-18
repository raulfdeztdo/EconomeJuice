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
    
    for (const root of possibleRoots) {
      const testScript = path.join(root, 'scripts', 'run_daily_analysis.sh');
      if (fs.existsSync(testScript)) {
        projectRoot = root;
        break;
      }
    }
    
    const scriptPath = path.join(projectRoot, 'scripts', 'run_daily_analysis.sh');
    
    // Verificar que el script existe
    if (!fs.existsSync(scriptPath)) {
      console.error('Script no encontrado en ninguna ubicación');
      console.error('Rutas probadas:', possibleRoots.map(root => path.join(root, 'scripts', 'run_daily_analysis.sh')));
      console.error('Directorio actual:', process.cwd());
      console.error('Contenido del directorio actual:', fs.readdirSync(process.cwd()));
      
      return {
        statusCode: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ 
          error: 'Script de análisis no encontrado',
          cwd: process.cwd(),
          tried_paths: possibleRoots.map(root => path.join(root, 'scripts', 'run_daily_analysis.sh'))
        })
      };
    }

    // Ejecutar el análisis
    return new Promise((resolve) => {
      exec(`bash "${scriptPath}"`, { 
        cwd: projectRoot,
        timeout: 300000, // 5 minutos timeout para Netlify
        env: { ...process.env, PATH: process.env.PATH + ':/usr/bin:/bin' }
      }, (error, stdout, stderr) => {
        if (error) {
          console.error('Error ejecutando análisis:', error);
          console.error('stderr:', stderr);
          
          // Crear timestamp de error
          const errorTimestamp = {
            last_update: new Date().toISOString(),
            status: 'error',
            message: `Error en actualización manual: ${error.message}`
          };
          
          // Intentar escribir el timestamp de error
          try {
            const errorPath = path.join(projectRoot, 'public', 'data', 'last_update.json');
            fs.writeFileSync(errorPath, JSON.stringify(errorTimestamp, null, 2));
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
              stderr: stderr
            })
          });
        } else {
          console.log('Análisis completado exitosamente');
          console.log('stdout:', stdout);
          
          resolve({
            statusCode: 200,
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({ 
              success: true, 
              message: 'Análisis ejecutado exitosamente',
              output: stdout
            })
          });
        }
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