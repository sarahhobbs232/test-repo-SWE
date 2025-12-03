--CREATE DATABASE

CREATE DATABASE Eternal_Elixers
USE Eternal_Elixers


--USER TABLE
CREATE TABLE User_T(
    UserID NUMERIC(11,0) NOT NULL,

    Username VARCHAR(50) NOT NULL,
    Password VARCHAR(50) NOT NULL,
    Name VARCHAR(25),
    Street VARCHAR(70),
    City VARCHAR(50),
    State VARCHAR(2),
    Zip NUMERIC(5),
    UserType VARCHAR(8),
CONSTRAINT User_PK PRIMARY KEY (UserID));

ALTER TABLE User_T
DROP COLUMN Street;

ALTER TABLE User_T
DROP COLUMN City;

ALTER TABLE User_T
DROP COLUMN State;

ALTER TABLE User_T
DROP COLUMN Zip;


INSERT INTO User_T VALUES (0001, 'ejones', 'password1', 'Eric Jones',  'Admin');
INSERT INTO User_T VALUES (0002, 'shobbs', 'password2', 'Sarah Hobbs',  'Admin');
INSERT INTO User_T VALUES (0003, 'kkolb', 'password3', 'Kyle Kolb',  'User');

SELECT *
FROM User_T;

SELECT *
FROM User_T
WHERE Usertype = 'Admin';


--BILL TABLE
CREATE TABLE Bill_T(
    BillID NUMERIC(11,0) NOT NULL,
    UserID NUMERIC(11,0),
    ShoppingCartID NUMERIC(11,0),
    ItemID NUMERIC(11,0),

    SalesDate DATE,
    SaleTime TIME,
    SalesTax DECIMAL(5,2),
    SubTotal MONEY,
    ShippingCost MONEY,
    Total MONEY,


CONSTRAINT Bill_PK PRIMARY KEY (BillID),
CONSTRAINT Bill_FK1 FOREIGN KEY (UserID) REFERENCES User_T(UserID),
CONSTRAINT Bill_FK2 FOREIGN KEY (ShoppingCartID) REFERENCES ShoppingCart_T(ShoppingCartID),
CONSTRAINT Bill_FK3 FOREIGN KEY (ItemID) REFERENCES Inventory_T(ItemID));


--Moved address info into Bill table since bill is being shipped to that specific address
ALTER TABLE Bill_T
ADD Street VARCHAR(250);

ALTER TABLE Bill_T
ADD City VARCHAR(250);

ALTER TABLE Bill_T
ADD State VARCHAR(2);

ALTER TABLE Bill_T
ADD Zip NUMERIC(5);


--adding ShippingID to Bill table check line 166
ALTER TABLE Bill_T
ADD ShippingID NUMERIC(11,0);

ALTER TABLE Bill_T
ADD CONSTRAINT Bill_FK4
FOREIGN KEY (ShippingID)
REFERENCES Shipping_T(ShippingID);



INSERT INTO Bill_T VALUES (1001, 0001, 5001, 3001, '12/17/2025', '12:35:56', .06, 12.00 , 29.00, 0.00, '1234 Main Street', 'Los Angeles', 'CA', '90210', 4001);
UPDATE Bill_T
SET Bill_T.Total = SubTotal + (SubTotal * .06) + ShippingCost
WHERE Bill_T.BillID = 1001;

INSERT INTO Bill_T VALUES (1002, 0002, 5002, 3002, '12/18/2025', '14:23:28', .06, 12.00, 29.00, 0.00, '5678 Hidden Valley Dr', 'Woodland Hills', 'CA', '91304', 4001);
UPDATE Bill_T
SET Total = SubTotal + (SubTotal * .06) + ShippingCost
WHERE Bill_T.BillID = 1002;

INSERT INTO Bill_T VALUES (1003, 0003, 5003, 3003,'12/23/2025', '09:18:54', .06, 14.00, 19.00, 0.00, '8732 Morrish Grove Ct', 'Encino', 'CA', '91300', 4002);
UPDATE Bill_T
SET Total = SubTotal + (SubTotal * .06) + ShippingCost
WHERE Bill_T.BillID = 1003;

SELECT *
FROM Bill_T;



--BILL INVENTORY ITEM TABLE
CREATE TABLE BillInventoryItem_T(
    BillInventoryItemID NUMERIC(11,0) NOT NULL,
    BillID NUMERIC(11,0),
    ItemID NUMERIC (11,0),


CONSTRAINT BillInventoryItem_PK PRIMARY KEY (BillInventoryItemID),
CONSTRAINT BillInventoryItem_FK1 FOREIGN KEY (BillID) REFERENCES Bill_T(BillID),
CONSTRAINT BillInventoryItem_FK2 FOREIGN KEY (ItemID) REFERENCES Inventory_T(ItemID));

INSERT INTO BillInventoryItem_T VALUES (6001, 1001, 3001);
INSERT INTO BillInventoryItem_T VALUES (6002, 1002, 3002);
INSERT INTO BillInventoryItem_T VALUES (6003, 1003, 3003);

SELECT *
FROM BillInventoryItem_T;

--INVENTORY TABLE
CREATE TABLE Inventory_T(
    ItemID NUMERIC(11,0) NOT NULL,

    PotionName VARCHAR(50),
    PotionCategory VARCHAR(25),
    PotionDescription VARCHAR(100),
    PotionCost MONEY,
CONSTRAINT Inventory_PK PRIMARY KEY (ItemID));

ALTER TABLE Inventory_T
ADD PotionPhoto VARCHAR(250);


INSERT INTO Inventory_T VALUES (3001, 'Love Potion', 'Emotion', 'Takes only 3 drops to make anyone yours. ', 12.00, 'love potion image path ');
INSERT INTO Inventory_T VALUES (3002, 'Fire Potion', 'Elemental', 'Creates a large flame that is indistinguishable.', 12.00, 'fire portion image path');
INSERT INTO Inventory_T VALUES (3003, 'Growth Potion', 'Mystic', 'Grants user a 3x - 10x body size increase depending on dosage.', 14.00, ' growth potion image path');



SELECT *
FROM Inventory_T;

--SHOPPING CART TABLE
CREATE TABLE ShoppingCart_T(
    ShoppingCartID NUMERIC(11,0) NOT NULL,
    UserID NUMERIC(11,0),
    ItemID NUMERIC(11,0),
    ShippingID NUMERIC(11,0),


CONSTRAINT ShoppingCart_PK PRIMARY KEY (ShoppingCartID),
CONSTRAINT ShoppingCart_FK1 FOREIGN KEY (UserID) REFERENCES User_T(UserID),
CONSTRAINT ShoppingCart_FK2 FOREIGN KEY (ItemID) REFERENCES Inventory_T(ItemID),
CONSTRAINT ShoppingCart_FK3 FOREIGN KEY (ShippingID) REFERENCES Shipping_T(ShippingID));

--shipping is not chosen in shopping cart
ALTER TABLE ShoppingCart_T
DROP COLUMN ShippingID;

INSERT INTO ShoppingCart_T VALUES (5001, 0001, 3001);
INSERT INTO ShoppingCart_T VALUES (5002, 0002, 3002);
INSERT INTO ShoppingCart_T VALUES (5003,0003, 3003);

SELECT *
FROM ShoppingCart_T;




--SHIPPING TABLE
CREATE TABLE Shipping_T(
    ShippingID NUMERIC(11,0) NOT NULL ,
    ShippingType VARCHAR(25) NOT NULL,
    ShippingCost MONEY NOT NULL,

CONSTRAINT Shipping_PK PRIMARY KEY (ShippingID));

INSERT INTO Shipping_T VALUES (4001, 'Overnight', 29.00);
INSERT INTO Shipping_T VALUES (4002, '3-Day', 19.00);
INSERT INTO Shipping_T VALUES (4003, 'Ground', 0.00);

SELECT *
FROM Shipping_T;

