# Frontend Guideline Document - MURDOCK

This document outlines the essential parts of the frontend of MURDOCK, our internal web-based tool built for processing transactions. It explains the overall structure, design choices, and technologies used in everyday language so that everyone, regardless of technical background, can understand how the interface is built and maintained.

## 1. Frontend Architecture

MURDOCK is designed as a single-page application (SPA) that uses a lightweight tech stack. We use plain HTML for structure, simple JavaScript for interactivity and form validation, and CSS for styling. This combination is chosen because it keeps things simple and efficient.

Our architecture supports:

*   **Scalability:** Even though we are using a basic tech stack, the code is modular and neatly organized to allow for future changes or additional features if needed.
*   **Maintainability:** By keeping the code plain and using easy-to-follow techniques, any developer on the team will be able to understand and maintain the project without extensive technical background.
*   **Performance:** A single-page approach reduces page reloads and speeds up user interactions. The simplicity in our design means that the app loads quickly and remains responsive.

## 2. Design Principles

MURDOCK follows a set of clear principles to ensure a great user experience:

*   **Usability:** The layout is clean and data-focused, ensuring that all the important information is in view, and that input forms are straightforward to complete.
*   **Accessibility:** We ensure that the design is accessible to all team members. This includes clear text, proper color contrast (especially important in dark mode), and simple navigation.
*   **Responsiveness:** The design adjusts well to different screen sizes or resolutions. Even though it's an internal tool, it is designed to work on various devices.
*   **Simplicity:** The user interface is designed to be minimal. The focus is on getting the work done easily, with a clear table layout for data and an intuitive navigation bar to move through the tool.

## 3. Styling and Theming

### Styling Approach

For MURDOCK, we use vanilla CSS supported by best practices. We follow a structured CSS methodology similar to BEM (Block Element Modifier) to keep our classes organized and our code reusable. This approach makes it easier to style components consistently.

### Theming and Dark Mode

A key feature of MURDOCK is its dark mode. We handle theming by setting up CSS variables for colors and fonts that can be toggled between the default (light) and dark modes. This guarantees a uniform look and feel across the app.

### Overall Design Style

*   **Style:** The overall design follows a modern flat design with a focus on simplicity. The interfaces are clean, with minimal decorative styling. This is ideal for a data-focused internal application.

*   **Color Palette:**

    *   Background (Dark Mode): #1A1A1A
    *   Primary Accent: #3498DB (a cool blue tone)
    *   Secondary Accent: #2ECC71 (a fresh green tone)
    *   Error/Alert: #E74C3C (a strong red tone)
    *   Text: #FFFFFF (in dark mode), #333333 (in light mode)

### Font

In line with the modern look, we use a clean sans-serif font such as 'Helvetica Neue', 'Arial', or similar. This ensures readability and a professional appearance.

## 4. Component Structure

Even though MURDOCK is a simple application, its code is organized into components. For example, the main form is treated as a component that can be reused or modified separately from other parts of the page. Components include:

*   The form for transactions, comments, and action selection.
*   Navigation bar for clear movement around the tool (even in a single-page setup, different sections may be navigable via smooth scrolling or visibility toggling).
*   Data display areas such as tables for showing logged transactions.

This component-based structure helps keep the code clean and makes it easier to update individual parts of the application.

## 5. State Management

Given the simplicity of the internal tool, we manage the state with basic JavaScript variables and functions. When a user fills in the form, the data is temporarily stored in these variables until the form is submitted. This simple approach works well for our needs, ensuring the data flows smoothly between the different parts of the form.

For a more robust application, one might consider using frameworks like Redux or Context API, but for MURDOCK, keeping it simple is key.

## 6. Routing and Navigation

MURDOCK is a single-page application, so traditional multi-page routing isn’t required. Instead:

*   **Navigation Bar:** A clear and intuitive navigation bar is provided at the top of the page. This allows users to jump to different sections of the tool quickly.
*   **Anchored Navigation:** We use anchors or smooth scroll effects for in-page navigation, ensuring that the user experience remains seamless and intuitive.

## 7. Performance Optimization

To ensure a smooth user experience, we follow several performance optimizations:

*   **Lazy Loading & Code Splitting:** While the application is small, techniques like lazy loading of non-critical assets ensure that the app loads fast.
*   **Asset Optimization:** Images, CSS, and JavaScript are kept lightweight. We use minification and compression where possible.
*   **Efficient DOM Manipulation:** Using JavaScript sparingly and efficiently prevents performance bottlenecks, keeping the interface responsive during interaction.

## 8. Testing and Quality Assurance

Even for a lightweight project like MURDOCK, it’s important to ensure that everything works as expected. Our approach includes:

*   **Unit Tests:** Small tests written for individual functions, particularly for input validation and form processing.
*   **Integration Testing:** We test how different parts of the application work together, ensuring that data flows correctly from the input form to the TXT file storage on the backend.
*   **Manual Testing:** Given the internal nature of the tool, periodic manual testing is conducted by designated team members to ensure usability and that any issues are found before wider use.
*   **Tools and Frameworks:** While we rely on simple JavaScript, tools like Windsurf (our modern IDE with AI coding capabilities) help ensure that our code is consistent and well-reviewed.

## 9. Conclusion and Overall Frontend Summary

To wrap up, the frontend of the MURDOCK project is built on a lightweight, single-page design that prioritizes simplicity, efficiency, and security. The combination of HTML, JavaScript, and CSS is more than sufficient for our needs:

*   The architecture supports the immediate processing of transactions with a clean, data-focused layout.
*   Clear design principles ensure usability, accessibility, and responsiveness, with a special nod to the dark mode option.
*   Styling follows a modern flat design, with a consistent color palette and font choices that match the professional look of the internal tool.
*   Organized component structure and straightforward state management allow the tool to be maintained and evolved simply.
*   Simple routing, performance optimizations, and rigorous testing all combine to offer a reliable and fast user experience.

This Frontend Guideline Document lays out all the key points of the MURDOCK project, ensuring that even someone without a technical background can understand how each part of the project fits together and contributes to a robust and efficient internal tool.

We trust that these guidelines will serve as a useful reference for current and future team members working on MURDOCK.
