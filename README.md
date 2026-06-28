# 🏠 Rentify

Rentify is a modern rental property management platform that connects property owners and tenants. It allows users to browse rental properties, manage listings, securely make payments, and communicate through an intuitive dashboard.

---

## ✨ Features

### 👤 User Features
- User Registration & Login
- Browse Rental Properties
- Advanced Property Search & Filters
- View Property Details
- Save Favorite Properties
- Book Rental Properties
- Stripe Secure Payment Gateway
- Booking History
- User Profile Management

### 🏡 Property Owner Features
- Add New Properties
- Edit Property Details
- Delete Listings
- Upload Property Images
- Manage Bookings
- View Payment History

### 🛡️ Admin Features
- Dashboard Overview
- Manage Users
- Manage Property Listings
- Monitor Bookings
- Payment Management
- System Analytics

---

## 🛠️ Tech Stack

### Frontend
- React.js
- Vite
- Tailwind CSS
- Axios
- React Router DOM

### Backend
- Node.js
- Express.js

### Database
- MongoDB
- Mongoose

### Authentication
- JWT (JSON Web Token)
- bcrypt

### Payment Gateway
- Stripe

### Cloud Storage
- Cloudinary (Property Images)

---

## 📁 Project Structure

```
Rentify
│
├── client/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── server/
│   ├── controllers/
│   ├── routes/
│   ├── models/
│   ├── middleware/
│   ├── config/
│   └── server.js
│
├── README.md
└── package.json
```

---

## ⚙️ Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/rentify.git
```

Move into the project

```bash
cd rentify
```

---

### Install Frontend

```bash
cd client
npm install
```

---

### Install Backend

```bash
cd ../server
npm install
```

---

## 🔑 Environment Variables

Create a `.env` file inside the **server** folder.

```env
PORT=5000

MONGO_URI=your_mongodb_connection_string

JWT_SECRET=your_secret_key

STRIPE_SECRET_KEY=your_stripe_secret_key

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

---

## ▶️ Running the Project

Start Backend

```bash
cd server
npm run dev
```

Start Frontend

```bash
cd client
npm run dev
```

Open your browser

```
http://localhost:5173
```

---

## 💳 Payment

Rentify uses **Stripe** for secure online payments.

Features include:

- Secure Checkout
- Payment Verification
- Booking Confirmation
- Transaction History

---

## 📸 Screenshots

Add screenshots here.

```
Home Page

Property Details

Dashboard

Payment Page
```

---

## 🚀 Future Improvements

- Chat Between Owner & Tenant
- Google Maps Integration
- Property Reviews
- Email Notifications
- Push Notifications
- AI Property Recommendation
- Multi-language Support
- Mobile Application

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit changes

```bash
git commit -m "Added new feature"
```

4. Push

```bash
git push origin feature-name
```

5. Create a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## ⭐ Support

If you like this project, please give it a ⭐ on GitHub.
