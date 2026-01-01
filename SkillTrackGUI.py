
def clear_screen():
    # 'nt' refers to Windows; 'posix' refers to Linux/macOS/Unix
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')
def pause():
    input("Press Enter to continue...")

# main

if __name__ == "__main__":
    from datetime import datetime, timedelta
    appRun = True
    while(appRun):
        clear_screen()
        print("Welcome to Skill Track!")
        print("1. Entity Management")
        print("2. Start a Session")
        print("3. End a Session")
        print("4. Generate Report")
        print("5. Exit")
        choice = int(input("Select an option: "))
        
        if(choice == 1):
            clear_screen()
            print("\nEntity Management")
            print("1. Add Entity")
            print("2. View Entities")
            entityChoice = int(input("Select an option: "))
            if(entityChoice == 1):
                name = input("Enter Entity Name:")
                type = input("Enter Entity Type (Skill/Project):")
                description = input("Enter Entity Description:")
                entity = Entity(id=len(loadEntitiesFromFile()) + 1, name=name, type=type, description=description)
                appendEntityToFile(entity)
                print("Entity added successfully!")
                pause()
            elif(entityChoice == 2):
                entities = loadEntitiesFromFile()
                clear_screen()
                print("Entities:")
                for entity in entities:
                    print(f"ID: {entity.id}, Name: {entity.name}, Type: {entity.type}, Description: {entity.description}")
                pause()
        elif(choice == 2):
            # print all entities
            entities = loadEntitiesFromFile()
            clear_screen()
            print("Entities:")
            for entity in entities:
                print(f"ID: {entity.id}, Name: {entity.name}, Type: {entity.type}, Description: {entity.description}")
            
            print("Select an entity by ID to start a session:")
            entityId = int(input())
            selectedEntity = next((e for e in entities if e.id == entityId), None)
            if selectedEntity:
                session = startSession(selectedEntity)
                print(f"Session started for {selectedEntity.name} at {session.startTime}")
            else:
                print("Invalid Entity ID")
            pause()
        elif(choice == 3):
            # print all started sessions
            clear_screen()
            print("Started Sessions:")
            startedSessions = loadStartedSessionsFromFile()
            for session in startedSessions:
                entity = next((e for e in loadEntitiesFromFile() if e.id == session.entityId), None)
                if entity:
                    print(f"Session ID: {session.id}, Entity: {entity.name}, Start Time: {session.startTime}")
            
            print("Select a session by ID to end:")
            sessionId = int(input())
            selectedSession = next((s for s in startedSessions if s.id == sessionId), None)
            if selectedSession:
                endedSession = endSession(selectedSession)
                print(f"Session ended at {endedSession.endTime}")
            else:
                print("Invalid Session ID")
            pause()
        elif(choice == 4):
            
        # print all entities
            clear_screen()
            print("1. View Report for a specific Entity")
            print("2. View Reports for all Entities (for last 7 days)")
            reportChoice = int(input("Select an option: "))
            if(reportChoice == 1):
                entities = loadEntitiesFromFile()
                clear_screen()
                print("Entities:")
                for entity in entities:
                    print(f"ID: {entity.id}, Name: {entity.name}, Type: {entity.type}, Description: {entity.description}")
                
                print("Select an entity by ID to generate report:")
                entityId = int(input())
                selectedEntity = next((e for e in entities if e.id == entityId), None)
                if selectedEntity:
                    report = GenerateReport(selectedEntity, datetime.now() - timedelta(days=7), datetime.now())
                    hours, minutes, seconds = report.totalTimeSpent
                    print(f"Report for {selectedEntity.name} from {report.startDate} to {report.endDate}: {hours} hours, {minutes} minutes, {seconds} seconds")
                else:
                    print("Invalid Entity ID")
                pause()
            elif(reportChoice == 2):
                print("Generating Reports for all Entities...")
                entities = loadEntitiesFromFile()
                Reports = []
                for entity in entities:
                    Reports.append(GenerateReport(entity, datetime.now() - timedelta(days=7), datetime.now()))
            
                for report in Reports:
                    entity = next((e for e in entities if e.id == report.entityId), None)
                    if entity:
                        hours, minutes, seconds = report.totalTimeSpent
                        print(f"Report for {entity.name} from {report.startDate} to {report.endDate}: {hours} hours, {minutes} minutes, {seconds} seconds")
                pause()
        elif(choice == 5):
            appRun = False
            print("Exiting Skill Track. Goodbye!")
        else:
            print("Invalid choice!")
            pause()
        
    