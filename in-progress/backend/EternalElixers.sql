-- EternalElixers.sql  (SQLite schema + seed data)
PRAGMA foreign_keys = ON;

-------------------------------------------------
-- USER TABLE
-------------------------------------------------
DROP TABLE IF EXISTS User_T;
CREATE TABLE User_T (
    UserID      INTEGER      PRIMARY KEY,
    Username    TEXT         NOT NULL UNIQUE,
    Password    TEXT         NOT NULL,
    Name        TEXT,
    UserType    TEXT         NOT NULL,
    Email       TEXT
);

INSERT INTO User_T (UserID, Username, Password, Name, UserType, Email) VALUES
(1, 'ejones', 'password1', 'Eric Jones',  'Admin', 'ejones@gmail.com'),
(2, 'shobbs', 'password2', 'Sarah Hobbs', 'Admin', 'shobbs@gmail.com'),
(3, 'kkolb',  'password3', 'Kyle Kolb',   'User',  'kkolb@gmail.com');

-------------------------------------------------
-- INVENTORY TABLE
-------------------------------------------------
DROP TABLE IF EXISTS Inventory_T;
CREATE TABLE Inventory_T (
    ItemID            INTEGER      PRIMARY KEY,
    PotionName        TEXT,
    PotionCategory    TEXT,
    PotionDescription TEXT,
    PotionCost        REAL,
    PotionPhoto       TEXT
);

INSERT INTO Inventory_T (ItemID, PotionName, PotionCategory, PotionDescription, PotionCost, PotionPhoto) VALUES
(3001, 'Love Potion',   'Emotion',   'Takes only 3 drops to make anyone yours.',          12.00, 'love potion image path'),
(3002, 'Fire Potion',   'Elemental', 'Creates a large flame that is indistinguishable.',  12.00, 'fire potion image path'),
(3003, 'Growth Potion', 'Mystic',    'Grants user a 3x - 10x body size increase.',       14.00, 'growth potion image path');

-------------------------------------------------
-- SHIPPING TABLE
-------------------------------------------------
DROP TABLE IF EXISTS Shipping_T;
CREATE TABLE Shipping_T (
    ShippingID   INTEGER   PRIMARY KEY,
    ShippingType TEXT      NOT NULL,
    ShippingCost REAL      NOT NULL
);

INSERT INTO Shipping_T (ShippingID, ShippingType, ShippingCost) VALUES
(4001, 'Overnight', 29.00),
(4002, '3-Day',     19.00),
(4003, 'Ground',     0.00);

-------------------------------------------------
-- SHOPPING CART TABLE
-------------------------------------------------
DROP TABLE IF EXISTS ShoppingCart_T;
CREATE TABLE ShoppingCart_T (
    ShoppingCartID INTEGER PRIMARY KEY,
    UserID         INTEGER,
    ItemID         INTEGER,
    FOREIGN KEY (UserID) REFERENCES User_T(UserID),
    FOREIGN KEY (ItemID) REFERENCES Inventory_T(ItemID)
);

INSERT INTO ShoppingCart_T (ShoppingCartID, UserID, ItemID) VALUES
(5001, 1, 3001),
(5002, 2, 3002),
(5003, 3, 3003);

-------------------------------------------------
-- BILL TABLE
-------------------------------------------------
DROP TABLE IF EXISTS Bill_T;
CREATE TABLE Bill_T (
    BillID         INTEGER    PRIMARY KEY,
    UserID         INTEGER,
    ShoppingCartID INTEGER,
    ItemID         INTEGER,
    SalesDate      TEXT,
    SaleTime       TEXT,
    SalesTax       REAL,
    SubTotal       REAL,
    ShippingCost   REAL,
    Total          REAL,
    Street         TEXT,
    City           TEXT,
    State          TEXT,
    Zip            TEXT,
    ShippingID     INTEGER,
    FOREIGN KEY (UserID)         REFERENCES User_T(UserID),
    FOREIGN KEY (ShoppingCartID) REFERENCES ShoppingCart_T(ShoppingCartID),
    FOREIGN KEY (ItemID)         REFERENCES Inventory_T(ItemID),
    FOREIGN KEY (ShippingID)     REFERENCES Shipping_T(ShippingID)
);

INSERT INTO Bill_T (BillID, UserID, ShoppingCartID, ItemID, SalesDate, SaleTime, SalesTax, SubTotal,
                    ShippingCost, Total, Street, City, State, Zip, ShippingID)
VALUES
(1001, 1, 5001, 3001, '2025-12-17', '12:35:56', 0.06, 12.00, 29.00, 0.00,
 '1234 Main Street', 'Los Angeles', 'CA', '90210', 4001),
(1002, 2, 5002, 3002, '2025-12-18', '14:23:28', 0.06, 12.00, 29.00, 0.00,
 '5678 Hidden Valley Dr', 'Woodland Hills', 'CA', '91304', 4001),
(1003, 3, 5003, 3003, '2025-12-23', '09:18:54', 0.06, 14.00, 19.00, 0.00,
 '8732 Morrish Grove Ct', 'Encino', 'CA', '91300', 4002);

-- compute Totals
UPDATE Bill_T
SET Total = SubTotal + (SubTotal * SalesTax) + ShippingCost;

-------------------------------------------------
-- BILL INVENTORY ITEM TABLE
-------------------------------------------------
DROP TABLE IF EXISTS BillInventoryItem_T;
CREATE TABLE BillInventoryItem_T (
    BillInventoryItemID INTEGER PRIMARY KEY,
    BillID              INTEGER,
    ItemID              INTEGER,
    FOREIGN KEY (BillID) REFERENCES Bill_T(BillID),
    FOREIGN KEY (ItemID) REFERENCES Inventory_T(ItemID)
);

INSERT INTO BillInventoryItem_T (BillInventoryItemID, BillID, ItemID) VALUES
(6001, 1001, 3001),
(6002, 1002, 3002),
(6003, 1003, 3003);

