// Test the new Vercel API endpoints
async function testAPI() {
    const testPayload = {
        skills: ["data analysis"],
        k: 3
    };

    try {
        console.log('Testing new search API...');
        const response = await fetch('http://localhost:5173/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testPayload)
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            return;
        }

        const result = await response.json();
        console.log('Search results:', JSON.stringify(result, null, 2));

    } catch (error) {
        console.error('Request failed:', error);
    }
}

testAPI();