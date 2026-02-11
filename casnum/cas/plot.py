import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
# Create a new figure and axis
fig, ax = plt.subplots()
# Store all elements to be added incrementally
elements = []
enable_graphics = True

def add_element(element):
    """Register a new element to be plotted."""
    elements.append(element)

def update(frame):
    """Update function for the animation."""
    ax.clear()
    for element in elements[:frame]:
        if isinstance(element, list):
            for artist in element:
                ax.add_artist(artist)
        else:
            ax.add_artist(element)
    
    ax.relim()
    ax.autoscale_view()

    return ax.artists

def show_plot():
    """Create the animation and show the plot."""
    ax.set_aspect('equal')

# Add labels and legend
    ax.set_title('Calculting (7)^(-1) mod 23')
    ax.set_xlabel('X-axis')
    ax.set_ylabel('Y-axis')
    ax.legend()
    print(len(elements))
    ani = FuncAnimation(fig, update, frames=len(elements) + 1, interval=5, blit=True)
    ani.save("xor.mp4", writer='ffmpeg', fps=24)
    plt.show()

def get_ax():
    """Return the global axis object."""
    return ax
