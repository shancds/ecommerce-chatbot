import ChatWidget from './components/ChatWidget';
import './App.css';

function App() {
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="headerContent">
          <div className="logo">E-Shop</div>
          <nav className="nav">
            <a href="#" className="navLink">Products</a>
            <a href="#" className="navLink">Orders</a>
            <a href="#" className="navLink">About</a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="main">
        <section className="hero">
          <h1 className="heroTitle">Welcome to E-Shop</h1>
          <p className="heroSubtitle">
            Click the chat bubble in the bottom-Right corner to talk with our AI assistant.
          </p>
        </section>

        <section className="features">
          <div className="featureCard">
            <div className="featureIcon">🛒</div>
            <h3 className="featureTitle">Easy Shopping</h3>
            <p className="featureDescription">
              Browse our catalog and find exactly what you need with our intuitive interface.
            </p>
          </div>

          <div className="featureCard">
            <div className="featureIcon">📦</div>
            <h3 className="featureTitle">Fast Delivery</h3>
            <p className="featureDescription">
              Get your orders delivered quickly with our reliable shipping partners.
            </p>
          </div>

          <div className="featureCard">
            <div className="featureIcon">💬</div>
            <h3 className="featureTitle">24/7 Support</h3>
            <p className="featureDescription">
              Our AI chatbot is always available to help with your questions and orders.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p className="footerText">© 2025 E-Shop...</p>
      </footer>

      <ChatWidget />

      <div className="chatHint">
        Need help? Click here!
      </div>
    </div>
  );
}

export default App;
