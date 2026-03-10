*ASSIGNMENT 06 – Industry-Level Microservices*
This assignment upgrades Assignment 05 to production-level architecture.
*1. JWT Authentication Service*
* Central auth-service
* Role-based access control
* Token validation at API Gateway
*2. Saga Pattern for Distributed Transactions*
    Order creation must use Saga orchestration:
    1. Create order (Pending)
    2. Reserve payment
    3. Reserve shipping
    4. Confirm order
    5. Compensate if failure
*3. Event Bus Integration*
    Replace direct REST coupling with asynchronous messaging.
    Suggested tools:
    * RabbitMQ
    * Kafka
*4. API Gateway Responsibilities*
    * Routing
    * Authentication validation
    * Logging
    * Rate limiting
    6
*5. Observability*
    * Centralized logging
    * Health endpoints
    * Metrics endpoint
    Advanced Deliverables
    1. Implement Saga pattern
    2. Integrate message broker
    3. Implement JWT
    4. Provide fault simulation
    5. Provide load testing results
    6. Architecture justification report
*6 Conclusion*
    This tutorial guided students through:
    * Monolithic architecture limitations
    * Microservice principles
    * Domain-Driven Design decomposition
    * Academic-level implementation
    * Industry-grade distributed system architecture
Students completing ASSIGNMENT 06 will understand real-world distributed architecture design.
