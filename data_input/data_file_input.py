import typer as typ

#creating an object with the typer module
app = typ.Typer()

#cli functions for the input of a file
@app.command()
def input_file(file: str,display_file: bool = True):
    #file = input("input a python csv file: ")
    if file:
        print(f"{file} recieved")
    else:
        print("Please append file name")

if __name__ == "__main__":
    app()