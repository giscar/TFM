#!/usr/bin/env python3
"""
Script de prueba para visualización de trayectorias.
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def generar_trayectoria():
    """Genera una trayectoria de ejemplo en 3D."""
    t = np.linspace(0, 10, 100)
    x = t
    y = np.sin(t)
    z = -2.5 * np.ones_like(t)  # Altura constante
    return x, y, z

def visualizar_trayectoria():
    """Visualiza una trayectoria 3D."""
    x, y, z = generar_trayectoria()
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.plot(x, y, z, 'b-', linewidth=2, label='Trayectoria')
    ax.scatter(x[0], y[0], z[0], c='g', s=100, label='Inicio')
    ax.scatter(x[-1], y[-1], z[-1], c='r', s=100, label='Fin')
    
    ax.set_xlabel('X (metros)')
    ax.set_ylabel('Y (metros)')
    ax.set_zlabel('Z (metros)')
    ax.set_title('Trayectoria de Vuelo Experimental')
    ax.legend()
    
    plt.show()

if __name__ == "__main__":
    print("🧪 Generando visualización experimental...")
    visualizar_trayectoria()
