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
    PotionPhoto       TEXT,
    IsSold            INTEGER      NOT NULL DEFAULT 0   -- 0 = available, 1 = sold
);

INSERT INTO Inventory_T (ItemID, PotionName, PotionCategory, PotionDescription, PotionCost, PotionPhoto, IsSold) VALUES
(3001, 'Love Potion',   'Emotion',   'Takes only 3 drops to make anyone yours.',          12.00, 'love_potion.png', 0),
(3002, 'Fire Potion',   'Elemental', 'Creates a large flame that is indistinguishable.',  12.00, 'fire_potion.png', 0),
(3003, 'Growth Potion', 'Mystic',    'Grants user a 3x - 10x body size increase.',       14.00, 'growth_potion.png', 0);

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

-- No seed rows here; all carts start empty.

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
    FOREIGN KEY (ShoppingCartID) REFERENCES ShoppingCart_T(ShoppingCartID) ON DELETE SET NULL,
    FOREIGN KEY (ItemID)         REFERENCES Inventory_T(ItemID),
    FOREIGN KEY (ShippingID)     REFERENCES Shipping_T(ShippingID)
);

-- No seed bills; sales report + order history start empty.

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

-- No seed bill items either.
