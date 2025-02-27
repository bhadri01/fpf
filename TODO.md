# TODO List for Backend Development

## **Authentication & Security**
- [x] Implement JWT-based authentication (login, register, logout, refresh token)
- [x] Implement Two-Factor Authentication (2FA) with OTP
- [x] Encrypt 2FA secret before storing in DB
- [x] Verify OTP before enabling 2FA
- [x] Implement secure password hashing
- [x] Implement email verification system
- [x] Implement forgot/reset password with email notification
- [x] Prevent continuous reset email requests (cooldown system)
- [ ] Implement brute-force protection for login attempts (Rate limiting)

## **API Key Authentication**
- [x] Implement API key creation & storage (secure hashing)
- [x] Implement API key validation in middleware
- [x] Implement API key deletion
- [ ] Implement API key expiration & rotation
- [ ] Implement role-based API key permissions

## **Middleware & Access Control**
- [x] Implement role-based access control (RBAC) using Redis cache
- [x] Implement permission middleware to check access rights
- [x] Allow API key authentication alongside JWT authentication
- [x] Allow public routes to be accessed without authentication
- [ ] Implement request rate limiting for API endpoints

## **User Management**
- [x] Implement user role management system
- [x] Implement user status (active, pending, blocked, paused)
- [ ] Implement user session tracking (Active sessions & logout all)

## **Database & Caching**
- [x] Use PostgreSQL as the main database
- [x] Implement Redis for caching permissions & authentication-related data
- [ ] Implement database connection pooling & optimization
- [ ] Implement scheduled cache invalidation

## **Logging & Monitoring**
- [x] Implement logging for authentication & security events
- [ ] Integrate structured logging for better debugging
- [ ] Implement API request logging & analytics

## **Admin Panel Features**
- [x] Implement admin panel for user & role management
- [x] Implement role-based permission assignment
- [ ] Implement audit logs for user activities
- [ ] Implement API key usage tracking

## **Future Enhancements**
- [ ] Implement OAuth2 / Social Login (Google, GitHub, etc.)
- [ ] Implement API rate limiting based on user roles
- [ ] Implement service-to-service authentication (internal API keys)
- [ ] Implement webhook security for external integrations
- [ ] Implement event-driven architecture using message queues (RabbitMQ)

## **Testing & Deployment**
- [x] Setup Docker for local development
- [x] Implement CI/CD pipeline for automated deployments
- [ ] Write unit tests for authentication & API key management
- [ ] Implement end-to-end testing for user authentication
- [ ] Optimize performance before production release

