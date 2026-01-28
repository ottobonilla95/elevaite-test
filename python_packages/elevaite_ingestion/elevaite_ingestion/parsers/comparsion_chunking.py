import pandas as pd
import matplotlib.pyplot as plt

# Define column names
columns = [
    "Chunk Index",
    "Sentence Object",
    "Context Aware Sentence Object",
    "Context Aware Sequential Semantic Chunk",
    "Context Aware Adaptive Chunk",
    "Context Aware Hybrid Chunk",
    "Context Aware Global Semantic Chunk",
    "Standard Semantic Chunker Output",
]

# Create an empty DataFrame
df_comparison = pd.DataFrame(columns=columns)

# Check if dataframe is empty
if df_comparison.empty:
    print("The dataframe is empty. Displaying placeholder table.")

    # Create placeholder data
    placeholder_data = [["-" for _ in columns]]  # Single row with "-" placeholders

    # Plot the table
    fig, ax = plt.subplots(figsize=(20, 10))
    ax.axis("tight")
    ax.axis("off")
    table = ax.table(
        cellText=placeholder_data, colLabels=columns, cellLoc="center", loc="center"
    )

    plt.title(
        "Comparison of Different Chunking Approaches (Placeholder Data)",
        fontsize=14,
        fontweight="bold",
    )
    plt.show()
else:
    fig, ax = plt.subplots(figsize=(20, 10))
    ax.axis("tight")
    ax.axis("off")
    table = ax.table(
        cellText=df_comparison.values,
        colLabels=df_comparison.columns,
        cellLoc="center",
        loc="center",
    )

    plt.title(
        "Comparison of Different Chunking Approaches", fontsize=18, fontweight="bold"
    )
    plt.show()
