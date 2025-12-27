import React from 'react';
import NavigationHeader from '../Shared/NavigationHeader';

const ContactPage = () => {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 50%, #dee2e6 100%)',
      fontFamily: 'Arial, sans-serif'
    }}>
      <NavigationHeader />
      <div style={{ padding: '220px 20px 60px 20px' }}>
      <div style={{
        maxWidth: '800px',
        margin: '0 auto',
        background: '#ffffff',
        borderRadius: '20px',
        padding: '50px',
        border: '1px solid #e0e0e0',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '50px' }}>
          <div style={{
            fontSize: '60px',
            marginBottom: '20px',
            background: 'linear-gradient(45deg, #e91e63, #f06292, #ff9800)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>✨</div>
          <h1 style={{
            color: '#333333',
            fontSize: '42px',
            marginBottom: '15px'
          }}>Contact AstroRoshni</h1>
          <p style={{
            color: '#666666',
            fontSize: '18px',
            lineHeight: '1.6'
          }}>Connect with us for your cosmic journey</p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
          gap: '30px',
          marginBottom: '40px'
        }}>
          <div style={{
            background: '#f8f9fa',
            borderRadius: '15px',
            padding: '40px',
            border: '1px solid #e0e0e0',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '50px', marginBottom: '20px' }}>📧</div>
            <h3 style={{ color: '#e91e63', marginBottom: '15px', fontSize: '24px' }}>Email Support</h3>
            <p style={{ color: '#666666', marginBottom: '20px' }}>Get help with your account, billing, or technical issues</p>
            <a href="mailto:help@astroroshni.com" style={{
              color: '#ffffff',
              fontSize: '18px',
              textDecoration: 'none',
              padding: '15px 30px',
              background: 'linear-gradient(135deg, #e91e63, #f06292)',
              borderRadius: '25px',
              display: 'inline-block',
              transition: 'all 0.3s ease',
              fontWeight: 'bold'
            }}>
              help@astroroshni.com
            </a>
          </div>

          <div style={{
            background: '#f8f9fa',
            borderRadius: '15px',
            padding: '40px',
            border: '1px solid #e0e0e0',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '50px', marginBottom: '20px' }}>💼</div>
            <h3 style={{ color: '#9c27b0', marginBottom: '15px', fontSize: '24px' }}>Business Inquiries</h3>
            <p style={{ color: '#666666', marginBottom: '20px' }}>Partnerships, collaborations, and business opportunities</p>
            <div style={{
              color: '#9c27b0',
              fontSize: '18px',
              padding: '15px 30px',
              background: '#f3e5f5',
              borderRadius: '25px',
              display: 'inline-block',
              fontWeight: 'bold'
            }}>
              Coming Soon
            </div>
          </div>
        </div>

        <div style={{
          background: '#f8f9fa',
          borderRadius: '15px',
          padding: '30px',
          border: '1px solid #e0e0e0',
          textAlign: 'center'
        }}>
          <h3 style={{ color: '#4caf50', marginBottom: '25px' }}>🌟 Follow Our Cosmic Journey</h3>
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '20px',
            flexWrap: 'wrap'
          }}>
            <a href="https://x.com/astroroshni" target="_blank" rel="noopener noreferrer" style={{
              background: 'linear-gradient(135deg, #1da1f2, #0d8bd9)',
              color: 'white',
              padding: '12px 20px',
              borderRadius: '25px',
              textDecoration: 'none',
              fontSize: '16px',
              fontWeight: 'bold',
              transition: 'transform 0.3s ease'
            }}>
              🐦 Twitter
            </a>
            <a href="https://instagram.com/astroroshniai" target="_blank" rel="noopener noreferrer" style={{
              background: 'linear-gradient(135deg, #e4405f, #c13584)',
              color: 'white',
              padding: '12px 20px',
              borderRadius: '25px',
              textDecoration: 'none',
              fontSize: '16px',
              fontWeight: 'bold',
              transition: 'transform 0.3s ease'
            }}>
              📷 Instagram
            </a>
            <a href="https://facebook.com/astroroshniai" target="_blank" rel="noopener noreferrer" style={{
              background: 'linear-gradient(135deg, #1877f2, #166fe5)',
              color: 'white',
              padding: '12px 20px',
              borderRadius: '25px',
              textDecoration: 'none',
              fontSize: '16px',
              fontWeight: 'bold',
              transition: 'transform 0.3s ease'
            }}>
              📘 Facebook
            </a>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
};

export default ContactPage;