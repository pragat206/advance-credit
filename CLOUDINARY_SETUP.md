# Cloudinary Setup Guide

## 🚀 Quick Setup (5 minutes)

### 1. Create Free Cloudinary Account
1. Go to [cloudinary.com](https://cloudinary.com)
2. Click "Sign Up For Free"
3. Complete the registration (no credit card required)

### 2. Get Your Credentials
1. After logging in, go to your **Dashboard**
2. Copy these values:
   - **Cloud Name** (e.g., `my-cloud-name`)
   - **API Key** (e.g., `123456789012345`)
   - **API Secret** (e.g., `abcdefghijklmnopqrstuvwxyz123456`)

### 3. Configure Your Application
1. Create a `.env` file in your project root (if it doesn't exist)
2. Add your Cloudinary credentials:

```env
# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-actual-cloud-name
CLOUDINARY_API_KEY=your-actual-api-key
CLOUDINARY_API_SECRET=your-actual-api-secret
```

### 4. Test the Setup
1. Start your application: `python -m uvicorn src.main_app.main:app --reload`
2. Go to `/blog/admin/login`
3. Login with: `admin@advancecred.com` / `Admin@2025`
4. Create a new post and upload an image
5. Check if the image appears correctly

## ✅ Benefits You'll Get

- **Free Storage**: 25GB storage, 25GB bandwidth/month
- **Automatic Optimization**: Images are automatically optimized for web
- **CDN**: Fast global delivery
- **No Server Storage**: Images stored in the cloud, not on your server
- **Reliable**: Images won't disappear when you deploy

## 🔧 Troubleshooting

### Images Not Uploading?
- Check your `.env` file has the correct credentials
- Make sure there are no extra spaces in the values
- Restart your application after adding credentials

### Images Not Displaying?
- Check the browser console for errors
- Verify the Cloudinary URL is being generated correctly
- Make sure your internet connection is working

## 📱 Free Tier Limits

- **Storage**: 25GB (plenty for blog images)
- **Bandwidth**: 25GB/month (good for moderate traffic)
- **Transformations**: 25,000/month (automatic optimizations)

## 🎯 Next Steps

Once set up, your blog will:
1. Upload images to Cloudinary automatically
2. Display optimized images with fast loading
3. Work reliably across all deployments
4. Scale with your traffic

Need help? Check the [Cloudinary Documentation](https://cloudinary.com/documentation) or contact support.
