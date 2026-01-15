
**Conversational AI Evaluation Tool - Version 1.0**

**Description**: 

This major release marks a foundational milestone for the Conversational AI Evaluation Tool. The platform now provides a unified, scalable, and extensible framework for evaluating conversational AI systems across multiple dimensions, languages, and evaluation strategies. The release focuses on modular design of interface manager, strategy improvements, and multilingual readiness

**Existing Features (Carried Forward)**

-   **ORM-Based Persistence Layer over MariaDB**  
    Robust object–relational mapping layer built on MariaDB, enabling structured storage and retrieval of evaluation data with transactional consistency.  

-   **Target and Test Run Management**  
    Support for defining evaluation targets and executing controlled test runs as part of the standard evaluation workflow.  

-   **Extensive Strategy Library**  
    Includes 43 evaluation strategies covering multiple dimensions of conversational AI assessment.

-   **Comprehensive Metrics Suite**  
    Provides 48 evaluation metrics to measure quality, safety, consistency, and robustness of conversational AI responses.

-   **Predefined Test Plans**  
    Ships with 7 curated test plans designed to address common conversational AI evaluation scenarios.  

-   **Large-Scale Test Case Repository**  
    Includes 400+ test cases, enabling broad coverage across domains, intents, and conversational patterns.  

-   **High-Performance Interface Manager Automation**  
    Optimized screen automation for faster, more reliable interaction with UI-driven target applications.
    
 **New Features**  
 
 - **Support for SQLite**
	Robust object–relational mapping layer built on **SQLite**, enabling lightweight, portable, file-based structured storage and reliable retrieval of evaluation data with transactional consistency.  

- **Enhanced and Extensible Interface Manager**  
    Introduces a modular interface manager architecture that supports easy integration of new target applications while maintaining isolation and stability across existing evaluation workflows.  
    
- **Separation of Automation Configuration from Core Logic**
	XPath definitions and credentials are externalized from the interface manager’s core codebase, allowing end users to adapt UI changes and authentication details without modifying or redeploying the system.

- **Support  for API-based target applications**
    Adds support for API-based target applications compatible with OpenAI-style interfaces, along with native evaluation support for WhatsApp Web and browser-based web applications.  

- **Refined Strategy Library**  
    Includes 43 improved evaluation strategies covering multiple dimensions of conversational AI assessment.  

- **Synthetic Dataset Support for Strategy Validation**  
    Enables the use of synthetic datasets to systematically validate, stress-test, and benchmark individual evaluation strategies under controlled and edge-case conversational scenarios.  

- **Test Data Management System (TDMS)**  
    Introduces a centralized system to create, update, and delete test cases directly in the database, ensuring structured test data governance, version control readiness, and scalability for large evaluation programs.