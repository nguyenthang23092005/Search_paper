import asyncio
import scholar_search
import springer_search


def run_all():
    print("🔹 Chạy camelai.py")
    scholar_search.main()  

    print("🔹 Chạy agent_spinger.py")
    asyncio.run(springer_search.main())  
 

if __name__ == "__main__":
    run_all()
