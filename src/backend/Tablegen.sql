-- Users table
CREATE TABLE Users (
    User_ID SERIAL PRIMARY KEY,
    Username VARCHAR(255) NOT NULL,
    Password VARCHAR(255) NOT NULL
);

-- Food table
CREATE TABLE Food (
    Food_ID SERIAL PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Calories INT NOT NULL
);

-- Catalog table
CREATE TABLE Catalog (
    Catalog_ID SERIAL PRIMARY KEY,
    User_ID INT NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID),
    Name VARCHAR(255) NOT NULL
);

-- Serving table (Join Table)
CREATE TABLE Serving (
    Catalog_ID INT NOT NULL,
    Food_ID INT NOT NULL,
    Name VARCHAR(255),
    PRIMARY KEY (Catalog_ID, Food_ID),
    FOREIGN KEY (Catalog_ID) REFERENCES Catalog(Catalog_ID) ON DELETE CASCADE,
    FOREIGN KEY (Food_ID) REFERENCES Food(Food_ID) ON DELETE CASCADE
);

-- Goals table
CREATE TABLE Goals (
    Goal_ID SERIAL PRIMARY KEY,
    User_ID INT NOT NULL,
    Weight FLOAT NOT NULL,
    Date_of_Goal DATE NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
);

-- Friends Table
CREATE TABLE Friends (
    Friends_ID SERIAL PRIMARY KEY,
    User_ID INT NOT NULL,
    Name VARCHAR(255),
    Date_of_Friendship DATE NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
);