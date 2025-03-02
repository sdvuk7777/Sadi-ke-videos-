import os
import re
import random
import string
from datetime import datetime
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler

# States for the conversation
UPLOAD_TXT = 0

async def html_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the HTML conversion process when /html command is used"""
    await update.message.reply_text("Please send your text file to convert to HTML.")
    return UPLOAD_TXT

async def process_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the text file when it's uploaded"""
    try:
        # Delete the user's message
        await update.message.delete()
        
        # Get the file
        file = await update.message.document.get_file()
        
        # Generate a random filename to store the file temporarily
        temp_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.txt'
        
        # Download the file
        await file.download_to_drive(temp_filename)
        
        # Read the content of the file
        with open(temp_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Delete the temporary file
        os.remove(temp_filename)
        
        # Generate HTML from the content
        html_content = generate_html(content)
        
        # Create a temporary HTML file
        html_filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) + '.html'
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Delete the existing message from bot if exists
        if hasattr(context, 'user_data') and 'last_message_id' in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data['last_message_id']
                )
            except Exception as e:
                print(f"Error deleting message: {e}")
        
        # Send processing message
        processing_msg = await update.effective_chat.send_message("Converting your txt file in HTML... 🕸 ")
        
        # Send the HTML file
        message = await update.effective_chat.send_document(
            document=open(html_filename, 'rb'),
            filename=f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            caption="✅ Your text file has been converted to HTML successfully!"
        )
        
        # Delete processing message
        await processing_msg.delete()
        
        # Store the message ID for future deletion
        if hasattr(context, 'user_data'):
            context.user_data['last_message_id'] = message.message_id
        
        # Delete the temporary HTML file
        os.remove(html_filename)
        
    except Exception as e:
        await update.effective_chat.send_message(f"❌ Error processing file: {str(e)}")
    
    return ConversationHandler.END

def generate_html(content):
    """Generate HTML from the text content"""
    # Extract lines from content
    lines = content.strip().split('\n')
    
    # Parse links and titles
    parsed_data = []
    for line in lines:
        if not line.strip():
            continue
            
        # Split by colon and URL
        parts = line.split(':', 1)
        if len(parts) == 2:
            title = parts[0].strip()
            url = parts[1].strip()
            parsed_data.append({
                'title': title,
                'url': url
            })
    
    # Categorize items
    pdf_items = []
    video_items = []
    other_items = []
    
    # Create a dictionary to group by course name
    course_groups = {}
    
    for item in parsed_data:
        title = item['title']
        url = item['url']
        
        # Extract course name (text before the first number)
        match = re.search(r'^(.*?)(?:\s+\d+\s*:|\s*$)', title)
        course_name = match.group(1).strip() if match else "Other"
        
        # Add to course groups
        if course_name not in course_groups:
            course_groups[course_name] = []
        course_groups[course_name].append(item)
        
        # Categorize by URL type
        if '.pdf' in url.lower():
            pdf_items.append(item)
        elif any(ext in url.lower() for ext in ['.mpd', '.m3u8', '.mp4', '.webm']):
            video_items.append(item)
        else:
            other_items.append(item)
    
    # HTML template with CSS and JavaScript
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML By SDV_BOTS</title>
    <style>
        :root {
            --primary-color: #4a6fa5;
            --secondary-color: #166088;
            --accent-color: #4fc3dc;
            --background-color: #f8f9fa;
            --card-color: #ffffff;
            --text-color: #333333;
            --border-color: #e1e4e8;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 20px 0;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        h1, h2, h3 {
            margin-bottom: 15px;
        }
        
        .search-container {
            display: flex;
            margin-bottom: 20px;
        }
        
        .search-input {
            flex: 1;
            padding: 12px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .search-input:focus {
            border-color: var(--accent-color);
        }
        
        .tabs {
            display: flex;
            background: var(--card-color);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .tab {
            padding: 15px 25px;
            flex: 1;
            text-align: center;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }
        
        .tab.active {
            background-color: var(--card-color);
            border-bottom: 3px solid var(--accent-color);
            color: var(--primary-color);
        }
        
        .content-section {
            display: none;
            animation: fadeIn 0.5s;
        }
        
        .content-section.active {
            display: block;
        }
        
        .course-accordion {
            margin-bottom: 15px;
            background: var(--card-color);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .course-header {
            padding: 15px 20px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s;
        }
        
        .course-header:hover {
            background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
        }
        
        .course-content {
            display: none;
            padding: 0;
        }
        
        .course-content.active {
            display: block;
        }
        
        .item {
            padding: 15px 20px;
            border-bottom: 1px solid var(--border-color);
            transition: background 0.3s;
        }
        
        .item:last-child {
            border-bottom: none;
        }
        
        .item:hover {
            background-color: rgba(74, 111, 165, 0.1);
        }
        
        .item a {
            text-decoration: none;
            color: var(--text-color);
            display: block;
        }
        
        /* Token Modal */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            animation: fadeIn 0.3s;
        }
        
        .modal-content {
            background-color: var(--card-color);
            margin: 10% auto;
            padding: 30px;
            border-radius: 10px;
            max-width: 500px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.3s;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .close {
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .modal input {
            width: 100%;
            padding: 12px;
            margin: 10px 0 20px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            font-size: 16px;
        }
        
        .modal button {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .modal button:hover {
            background: linear-gradient(135deg, var(--secondary-color), var(--primary-color));
            transform: translateY(-2px);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        @keyframes slideIn {
            from { transform: translateY(-30px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        /* No results message */
        .no-results {
            text-align: center;
            padding: 20px;
            background: var(--card-color);
            border-radius: 10px;
            margin-top: 20px;
            display: none;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
            .tabs {
                flex-direction: column;
            }
            
            .tab {
                border-right: none;
                border-bottom: 1px solid var(--border-color);
            }
            
            .tab.active {
                border-right: none;
                border-bottom: 3px solid var(--accent-color);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>SDV_BOTS</h1>
            <p>Browse and access your content easily</p>
        </header>
        
        <div class="search-container">
            <input type="text" class="search-input" placeholder="Search content..." id="searchInput">
        </div>
        
        <div class="tabs">
            <div class="tab active" data-tab="pdf">PDF</div>
            <div class="tab" data-tab="video">Video</div>
            <div class="tab" data-tab="other">Others</div>
        </div>
        
        <div id="pdfSection" class="content-section active">
            <h2>PDF Content</h2>
            <div id="pdfContent">
            </div>
        </div>
        
        <div id="videoSection" class="content-section">
            <h2>Video Content</h2>
            <div id="videoContent">
            </div>
        </div>
        
        <div id="otherSection" class="content-section">
            <h2>Other Content</h2>
            <div id="otherContent">
            </div>
        </div>
        
        <div class="no-results" id="noResults">
            <h3>No results found</h3>
            <p>Try different search terms</p>
        </div>
    </div>
    
    <!-- Token Modal -->
    <div id="tokenModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>Enter PW Token</h2>
                <span class="close">&times;</span>
            </div>
            <p>Please enter an active PW token to access the content:</p>
            <input type="text" id="tokenInput" placeholder="Enter your token here">
            <button id="submitToken">Submit</button>
        </div>
    </div>
    
    <script>
        // Store all the content data
        const contentData = {
            courses: {
            }
        };
        
        // Store the token
        let userToken = "";
        
        // Initialize data and event listeners when document is ready
        document.addEventListener('DOMContentLoaded', function() {
            // Show token modal on page load
            document.getElementById('tokenModal').style.display = 'block';
            
            // Close modal when clicking the × button
            document.querySelector('.close').addEventListener('click', function() {
                document.getElementById('tokenModal').style.display = 'none';
            });
            
            // Submit token
            document.getElementById('submitToken').addEventListener('click', function() {
                userToken = document.getElementById('tokenInput').value.trim();
                if (userToken) {
                    document.getElementById('tokenModal').style.display = 'none';
                    initializeContent();
                } else {
                    alert('Please enter a valid token');
                }
            });
            
            // Handle tab switching
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    // Remove active class from all tabs
                    tabs.forEach(t => t.classList.remove('active'));
                    // Add active class to clicked tab
                    this.classList.add('active');
                    
                    // Hide all content sections
                    document.querySelectorAll('.content-section').forEach(section => {
                        section.classList.remove('active');
                    });
                    
                    // Show corresponding content section
                    const tabName = this.getAttribute('data-tab');
                    document.getElementById(tabName + 'Section').classList.add('active');
                });
            });
            
            // Handle search functionality
            document.getElementById('searchInput').addEventListener('input', function() {
                searchContent(this.value.toLowerCase());
            });
        });
        
        function initializeContent() {
            // Load course data
            loadCourseData();
            
            // Render content for each section
            renderContent('pdf', 'pdfContent');
            renderContent('video', 'videoContent');
            renderContent('other', 'otherContent');
            
            // Add event listeners to course headers after content is loaded
            setupAccordions();
        }
        
        function loadCourseData() {
            // This is where we would dynamically populate the contentData object
            // For now, we'll hardcode it based on the parsed data
'''
    
    # Add JavaScript data population
    html += '''
            // PDF Courses
            contentData.courses.pdf = {};
'''
    
    # Populate course groups into JavaScript
    for course_name, items in course_groups.items():
        pdf_course_items = [item for item in items if '.pdf' in item['url'].lower()]
        if pdf_course_items:
            html += f'''
            contentData.courses.pdf["{course_name}"] = [
'''
            for item in pdf_course_items:
                html += f'''
                {{
                    title: "{item['title']}",
                    url: "{item['url']}"
                }},'''
            html += '''
            ];
'''
    
    html += '''
            // Video Courses
            contentData.courses.video = {};
'''
    
    # Populate video course groups
    for course_name, items in course_groups.items():
        video_course_items = [item for item in items if any(ext in item['url'].lower() for ext in ['.mpd', '.m3u8', '.mp4', '.webm'])]
        if video_course_items:
            html += f'''
            contentData.courses.video["{course_name}"] = [
'''
            for item in video_course_items:
                url = item['url']
                # Transform mpd URLs to the required format
                if "master.mpd" in url:
                    # Extract the ID part from the URL
                    match = re.search(r'cloudfront\.net/([^/]+)/master\.mpd', url)
                    if match:
                        video_id = match.group(1)
                        transformed_url = f"https://madxapi-d0cbf6ac738c.herokuapp.com/{video_id}/master.m3u8?token={{userToken}}"
                        html += f'''
                {{
                    title: "{item['title']}",
                    url: "{transformed_url}",
                    originalUrl: "{url}"
                }},'''
                else:
                    html += f'''
                {{
                    title: "{item['title']}",
                    url: "{url}"
                }},'''
            html += '''
            ];
'''
    
    html += '''
            // Other Courses
            contentData.courses.other = {};
'''
    
    # Populate other course groups
    for course_name, items in course_groups.items():
        other_course_items = [item for item in items if not any(ext in item['url'].lower() for ext in ['.pdf', '.mpd', '.m3u8', '.mp4', '.webm'])]
        if other_course_items:
            html += f'''
            contentData.courses.other["{course_name}"] = [
'''
            for item in other_course_items:
                html += f'''
                {{
                    title: "{item['title']}",
                    url: "{item['url']}"
                }},'''
            html += '''
            ];
'''
    
    # Add the rest of the JavaScript functions
    html += '''
        }
        
        function renderContent(type, containerId) {
            const container = document.getElementById(containerId);
            container.innerHTML = ''; // Clear container
            
            const courses = contentData.courses[type];
            if (!courses || Object.keys(courses).length === 0) {
                container.innerHTML = '<p>No content available in this section.</p>';
                return;
            }
            
            // Sort course names alphabetically
            const sortedCourseNames = Object.keys(courses).sort();
            
            for (const courseName of sortedCourseNames) {
                const items = courses[courseName];
                
                // Create accordion
                const accordionDiv = document.createElement('div');
                accordionDiv.className = 'course-accordion';
                accordionDiv.dataset.type = type;
                accordionDiv.dataset.course = courseName;
                
                // Create header
                const headerDiv = document.createElement('div');
                headerDiv.className = 'course-header';
                headerDiv.innerHTML = `<h3>${courseName}</h3><span>+</span>`;
                
                // Create content container
                const contentDiv = document.createElement('div');
                contentDiv.className = 'course-content';
                
                // Add items to content
                for (const item of items) {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'item';
                    
                    // Create link element
                    const link = document.createElement('a');
                    link.textContent = item.title;
                    
                    // Handle URL processing for video links
                    if (type === 'video' && item.originalUrl && item.originalUrl.includes('master.mpd')) {
                        link.href = item.url.replace('{userToken}', userToken);
                        link.target = '_blank';
                    } else {
                        link.href = item.url;
                        link.target = '_blank';
                    }
                    
                    itemDiv.appendChild(link);
                    contentDiv.appendChild(itemDiv);
                }
                
                // Assemble accordion
                accordionDiv.appendChild(headerDiv);
                accordionDiv.appendChild(contentDiv);
                
                // Add to container
                container.appendChild(accordionDiv);
            }
        }
        
        function setupAccordions() {
            const accordionHeaders = document.querySelectorAll('.course-header');
            
            accordionHeaders.forEach(header => {
                header.addEventListener('click', function() {
                    // Toggle active class on content
                    const content = this.nextElementSibling;
                    content.classList.toggle('active');
                    
                    // Update the + / - indicator
                    const indicator = this.querySelector('span');
                    indicator.textContent = content.classList.contains('active') ? '-' : '+';
                });
            });
        }
        
        function searchContent(query) {
            if (!query) {
                // Show all content if search is empty
                document.querySelectorAll('.course-accordion').forEach(accordion => {
                    accordion.style.display = 'block';
                });
                document.getElementById('noResults').style.display = 'none';
                return;
            }
            
            let resultsFound = false;
            
            // Search through all accordions
            document.querySelectorAll('.course-accordion').forEach(accordion => {
                const type = accordion.dataset.type;
                const courseName = accordion.dataset.course;
                const items = contentData.courses[type][courseName];
                
                // Check if course name matches
                const courseMatches = courseName.toLowerCase().includes(query);
                
                // Check if any items match
                const itemMatches = items.some(item => item.title.toLowerCase().includes(query));
                
                // Show/hide accordion based on matches
                if (courseMatches || itemMatches) {
                    accordion.style.display = 'block';
                    resultsFound = true;
                    
                    // If search matches course name, expand it
                    if (courseMatches) {
                        const content = accordion.querySelector('.course-content');
                        const indicator = accordion.querySelector('.course-header span');
                        
                        content.classList.add('active');
                        indicator.textContent = '-';
                    }
                    
                    // Highlight matching items
                    const itemElements = accordion.querySelectorAll('.item');
                    itemElements.forEach((itemElement, index) => {
                        if (items[index].title.toLowerCase().includes(query)) {
                            itemElement.style.display = 'block';
                            // Highlight the matching text
                            const link = itemElement.querySelector('a');
                            const title = items[index].title;
                            const highlightedTitle = title.replace(
                                new RegExp(query, 'gi'), 
                                match => `<span style="background-color: #ffeb3b;">${match}</span>`
                            );
                            link.innerHTML = highlightedTitle;
                        } else {
                            itemElement.style.display = courseMatches ? 'block' : 'none';
                        }
                    });
                } else {
                    accordion.style.display = 'none';
                }
            });
            
            // Show/hide no results message
            document.getElementById('noResults').style.display = resultsFound ? 'none' : 'block';
        }
    </script>
</body>
</html>
'''
    
    return html

# Define the handler
html_handler = ConversationHandler(
    entry_points=[CommandHandler('html', html_command)],
    states={
        UPLOAD_TXT: [MessageHandler(filters.Document.TEXT, process_txt_file)]
    },
    fallbacks=[],
    per_message=False
)