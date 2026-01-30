### **Conversational AI Evaluation Tool - Version 1.0.1**

#### **Description**: 

This release builds upon the foundational architecture of version 1.0 with significant enhancements to documentation, test data management, and API integration. Version 1.0.1 introduces comprehensive user manuals, streamlined test planning and metrics management capabilities, and improved API-driven automation workflows for evaluating conversational AI systems across multiple evaluation strategies.

#### **Existing Features (Carried Forward)**

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
 
- **Support for SQLite**
	Robust object–relational mapping layer built on **SQLite**, enabling lightweight, portable, file-based structured storage and reliable retrieval of evaluation data with transactional consistency.

- **Enhanced and Extensible Interface Manager**  
    Introduces a modular interface manager architecture that supports easy integration of new target applications while maintaining isolation and stability across existing evaluation workflows.  
    
- **Separation of Automation Configuration from Core Logic**
	XPath definitions and credentials are externalized from the interface manager’s core codebase, allowing end users to adapt UI changes and authentication details without modifying or redeploying the system.

- **Support for API-based target applications**
    Adds support for API-based target applications compatible with OpenAI-style interfaces, along with native evaluation support for WhatsApp Web and browser-based web applications.  

- **Refined Strategy Library**  
    Includes 43 improved evaluation strategies covering multiple metrics of conversational AI assessment.  

- **Synthetic Dataset Support for Strategy Validation**  
    Enables the use of synthetic datasets to systematically validate, stress-test, and benchmark individual evaluation strategies under controlled and edge-case conversational scenarios.  

- **Test Data Management System (TDMS)**  
    Introduces a web application based centralized system to create, update, and delete test cases directly in the database, ensuring structured test data governance, version control readiness, and scalability for large evaluation programs.

#### **New Features**

-   **Comprehensive Documentation Suite**  
    Updated README with setup instructions, configuration guidelines, and usage workflows. Includes technical documentation on system architecture, component interactions, and extensibility. Accompanied by a TDMS user manual with step-by-step guidance for test data management.

-   **Test Plan and Metrics Management**  
    Expanded the Test Data Management System (TDMS) with full CRUD capabilities for both test plans and evaluation metrics. This enhancement supports seamless creation, modification test plan configurations and custom metrics.

-   **Refactored Interface Manager with Improved API Logging**  
    Refactored the interface manager to align API logging with the other interface options, such as WhatsApp and WebApp. Enhancements include logging of prompt submissions and response retrieval, ensuring detailed audit trails and actionable performance insights.


### **Conversational AI Evaluation Tool - Version 1.0**

#### **Description**: 

This major release marks a foundational milestone for the Conversational AI Evaluation Tool. The platform now provides a unified, scalable, and extensible framework for evaluating conversational AI systems across multiple dimensions, languages, and evaluation strategies. The release focuses on modular design of interface manager, strategy improvements, and multilingual readiness

#### **Existing Features (Carried Forward)**

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
    
 #### **New Features**  
 
- **Support for SQLite**
	Robust object–relational mapping layer built on **SQLite**, enabling lightweight, portable, file-based structured storage and reliable retrieval of evaluation data with transactional consistency.

- **Enhanced and Extensible Interface Manager**  
    Introduces a modular interface manager architecture that supports easy integration of new target applications while maintaining isolation and stability across existing evaluation workflows.  
    
- **Separation of Automation Configuration from Core Logic**
	XPath definitions and credentials are externalized from the interface manager’s core codebase, allowing end users to adapt UI changes and authentication details without modifying or redeploying the system.

- **Support for API-based target applications**
    Adds support for API-based target applications compatible with OpenAI-style interfaces, along with native evaluation support for WhatsApp Web and browser-based web applications.  

- **Refined Strategy Library**  
    Includes 43 improved evaluation strategies covering multiple metrics of conversational AI assessment.  

- **Synthetic Dataset Support for Strategy Validation**  
    Enables the use of synthetic datasets to systematically validate, stress-test, and benchmark individual evaluation strategies under controlled and edge-case conversational scenarios.  

- **Test Data Management System (TDMS)**  
    Introduces a web application based centralized system to create, update, and delete test cases directly in the database, ensuring structured test data governance, version control readiness, and scalability for large evaluation programs.
