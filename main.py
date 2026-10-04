import ttkbootstrap as ttk


def main():
    root = ttk.Window(
        title="Quan ly kho nguyen lieu quan an",
        themename="flatly",
        size=(1000, 650)
    )

    label = ttk.Label(
        root,
        text="QUAN LY KHO NGUYEN LIEU QUAN AN",
        font=("Arial", 22, "bold")
    )
    label.pack(pady=30)

    root.mainloop()


if __name__ == "__main__":
    main()